"""Classificação, agregação e chaves de município.

Todas as funções tratam identificadores (código de município, CNES, CID) como
texto. Nenhuma função lê arquivos: recebem DataFrames já carregados pelo
caderno e devolvem DataFrames agregados.
"""

from __future__ import annotations

import pandas as pd

# Grupos de CID-10 do PLANO.md, seção 1 (desfechos e placebo).
# Cada grupo é um intervalo fechado de categorias de 3 caracteres.
GRUPOS_CID: dict[str, tuple[str, str]] = {
    "hipertensao": ("I10", "I15"),
    "avc": ("I60", "I69"),
    "diabetes": ("E10", "E14"),
    "apendicite": ("K35", "K38"),  # desfecho placebo
}
GRUPO_OUTRAS = "outras"  # demais diagnósticos (para totais e conferência)

# Código do tipo de estabelecimento "Polo Academia da Saúde" no CNES.
TP_UNID_POLO = "74"


def normalizar_cid(cid: pd.Series) -> pd.Series:
    """Padroniza o CID-10: texto, maiúsculas, sem ponto nem espaços."""
    return (
        cid.astype("string")
        .str.upper()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
    )


def classificar_cid(cid: pd.Series) -> pd.Series:
    """Devolve o grupo de CID (ver GRUPOS_CID) de cada diagnóstico, ou <NA>.

    A comparação usa a categoria de 3 caracteres (letra + 2 dígitos), de modo
    que "I109" e "I10" caem no mesmo grupo.
    """
    categoria = normalizar_cid(cid).str[:3]
    grupo = pd.Series(pd.NA, index=cid.index, dtype="string")
    valida = categoria.str.fullmatch(r"[A-Z][0-9]{2}").fillna(False)
    for nome, (ini, fim) in GRUPOS_CID.items():
        no_grupo = valida & (categoria >= ini) & (categoria <= fim)
        grupo = grupo.mask(no_grupo, nome)
    return grupo


def cod_ibge7_para_cod6(cod7: pd.Series) -> pd.Series:
    """Remove o dígito verificador: código IBGE de 7 dígitos -> 6 do DATASUS."""
    cod7 = cod7.astype("string").str.strip()
    if not cod7.str.fullmatch(r"[0-9]{7}").all():
        raise ValueError("Há códigos IBGE que não têm exatamente 7 dígitos.")
    return cod7.str[:6]


def normalizar_cod6(cod: pd.Series) -> pd.Series:
    """Padroniza código de município do DATASUS para 6 dígitos (texto)."""
    cod = cod.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return cod.str[:6]


COD6_BRASILIA = "530010"


def unificar_distrito_federal(cod6: pd.Series) -> pd.Series:
    """Leva qualquer código do DF (53xxxx) para Brasília (530010).

    O DF é um único município no IBGE, mas o DATASUS registra parte das
    ocorrências com códigos de regiões administrativas (ex.: 530040, 530180).
    """
    cod6 = cod6.astype("string")
    return cod6.mask(cod6.str.startswith("53"), COD6_BRASILIA)


def somar_por_municipio(df: pd.DataFrame, chaves: list[str], valores: list[str]) -> pd.DataFrame:
    """Unifica o DF em 530010 e soma `valores` por `chaves` (que incluem cod6)."""
    df = df.assign(cod6=unificar_distrito_federal(df["cod6"]))
    return df.groupby(chaves, as_index=False)[valores].sum()


def _numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype("string").str.strip(), errors="coerce")


# --------------------------------------------------------------------- SIH
def agregar_sih(
    rd: pd.DataFrame,
    col_mun: str = "MUNIC_RES",
    col_ano: str = "ANO_CMPT",
    col_cid: str = "DIAG_PRINC",
    col_ident: str = "IDENT",
) -> pd.DataFrame:
    """Conta AIHs por município de residência × ano × grupo de CID × tipo de AIH.

    Diagnósticos fora dos grupos de interesse entram como "outras", para que o
    total possa ser conferido com o TabNet. O tipo de AIH (`IDENT`: 1 = normal,
    5 = longa permanência) é mantido como dimensão; o filtro é feito depois,
    com a contagem registrada no caderno.
    Devolve colunas: cod6, ano, grupo, ident, internacoes.
    """
    base = pd.DataFrame(
        {
            "cod6": normalizar_cod6(rd[col_mun]),
            "ano": _numero(rd[col_ano]).astype("Int64"),
            "grupo": classificar_cid(rd[col_cid]).fillna(GRUPO_OUTRAS),
            "ident": (
                rd[col_ident].astype("string").str.strip()
                if col_ident in rd.columns
                else pd.Series(pd.NA, index=rd.index, dtype="string")
            ).fillna("ausente"),
        }
    )
    base = base.dropna(subset=["ano", "cod6"])
    return (
        base.groupby(["cod6", "ano", "grupo", "ident"], observed=True)
        .size()
        .rename("internacoes")
        .reset_index()
    )


# -------------------------------------------------------------------- CNES
def contar_polos(
    st: pd.DataFrame,
    ano: int,
    col_mun: str = "CODUFMUN",
    col_tipo: str = "TP_UNID",
    col_cnes: str = "CNES",
) -> pd.DataFrame:
    """Conta estabelecimentos tipo 74 por município numa competência do CNES-ST.

    Devolve colunas: cod6, ano, n_polos (apenas municípios com ao menos 1 polo).
    """
    tipo = st[col_tipo].astype("string").str.strip().str.zfill(2)
    polos = st.loc[tipo == TP_UNID_POLO, [col_mun, col_cnes]].copy()
    polos["cod6"] = normalizar_cod6(polos[col_mun])
    contagem = (
        polos.drop_duplicates(subset=[col_cnes])
        .groupby("cod6")
        .size()
        .rename("n_polos")
        .reset_index()
    )
    contagem["ano"] = ano
    return contagem[["cod6", "ano", "n_polos"]]


def primeiro_ano_tratamento(polos: pd.DataFrame, col_n: str = "n_polos") -> pd.Series:
    """Coorte g: primeiro ano em que o município tem ao menos um polo.

    Recebe o painel longo (cod6, ano, n_polos) e devolve uma Series indexada
    por cod6. Municípios sem polo não aparecem (o caderno atribui g = 0).
    """
    com_polo = polos.loc[polos[col_n] > 0]
    return com_polo.groupby("cod6")["ano"].min().rename("g")


def _competencia(serie: pd.Series) -> pd.Series:
    """Competência como número AAAAMM; vazio, zeros ou 999999 viram <NA>."""
    num = pd.to_numeric(serie.astype("string").str.replace(r"\D", "", regex=True),
                        errors="coerce")
    return num.where((num > 0) & (num < 999999))


def contar_incentivos(
    inc: pd.DataFrame,
    ano: int,
    codigos: set[str],
    col_incentivo: str = "SGRUPHAB",
    col_mun: str = "CODUFMUN",
    col_cnes: str = "CNES",
    competencia: int | None = None,
    col_inicio: str = "CMPT_INI",
    col_fim: str = "CMPT_FIM",
) -> pd.DataFrame:
    """Conta estabelecimentos com algum dos incentivos `codigos` (CNES-IN).

    Os códigos são comparados só pelos dígitos (\"81.12\" == \"8112\").
    Se `competencia` (AAAAMM) for dada e as colunas de vigência existirem, conta
    só os incentivos vigentes nela: início <= competência e fim vazio ou >= ela.
    Devolve colunas: cod6, ano, n_estab_incentivo.
    """
    alvo = {c.replace(".", "") for c in codigos}
    codigo = inc[col_incentivo].astype("string").str.replace(r"\D", "", regex=True)
    manter = codigo.isin(alvo)
    if competencia is not None and {col_inicio, col_fim} <= set(inc.columns):
        inicio, fim = _competencia(inc[col_inicio]), _competencia(inc[col_fim])
        vigente = (inicio.isna() | (inicio <= competencia)) & (fim.isna() | (fim >= competencia))
        manter &= vigente.fillna(True)
    sel = inc.loc[manter, [col_mun, col_cnes]].copy()
    sel["cod6"] = normalizar_cod6(sel[col_mun])
    contagem = (
        sel.drop_duplicates(subset=[col_cnes])
        .groupby("cod6")
        .size()
        .rename("n_estab_incentivo")
        .reset_index()
    )
    contagem["ano"] = ano
    return contagem[["cod6", "ano", "n_estab_incentivo"]]


def somar_leitos(
    lt: pd.DataFrame,
    col_mun: str = "CODUFMUN",
    col_sus: str = "QT_SUS",
    col_exist: str = "QT_EXIST",
) -> pd.DataFrame:
    """Soma leitos SUS e existentes por município (CNES-LT de uma competência)."""
    base = pd.DataFrame(
        {
            "cod6": normalizar_cod6(lt[col_mun]),
            "leitos_sus": _numero(lt[col_sus]).fillna(0),
            "leitos_existentes": _numero(lt[col_exist]).fillna(0),
        }
    )
    return base.groupby("cod6", as_index=False)[["leitos_sus", "leitos_existentes"]].sum()


def _data(serie: pd.Series) -> pd.Series:
    """Converte datas do DATASUS (AAAAMMDD ou ISO); o resto vira NaT."""
    texto = serie.astype("string").str.strip()
    d1 = pd.to_datetime(texto, format="%Y%m%d", errors="coerce")
    d2 = pd.to_datetime(texto, format="ISO8601", errors="coerce")
    return d1.fillna(d2)


def contar_equipes(
    ep: pd.DataFrame,
    col_mun: str = "CODUFMUN",
    col_tipo: str = "TIPO_EQP",
    col_desativacao: str = "DT_DESAT",
    data_referencia: str | None = None,
) -> pd.DataFrame:
    """Conta equipes ativas por município e tipo de equipe (CNES-EP).

    Se `data_referencia` (ex.: "2010-12-31") for dada e a coluna de desativação
    existir, descarta só as equipes com data de desativação válida até essa
    data; valores vazios ou que não são datas (ex.: zeros) contam como ativas.
    A escolha de quais tipos contam como Saúde da Família ou NASF é feita no
    caderno, a partir do dicionário de rótulos.
    Devolve colunas: cod6, tipo_eqp, n_equipes.
    """
    ativas = ep
    if data_referencia is not None and col_desativacao in ep.columns:
        desativacao = _data(ep[col_desativacao])
        ativas = ep.loc[(desativacao.isna() | (desativacao > pd.Timestamp(data_referencia))).values]
    base = pd.DataFrame(
        {
            "cod6": normalizar_cod6(ativas[col_mun]),
            "tipo_eqp": ativas[col_tipo].astype("string").str.strip(),
        }
    )
    return base.groupby(["cod6", "tipo_eqp"]).size().rename("n_equipes").reset_index()


# --------------------------------------------------------------- população
def interpolar_populacao(pop: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Completa os anos sem estimativa por interpolação linear, por município.

    Recebe colunas cod6, ano, populacao (anos ausentes podem faltar ou ser NaN).
    Só interpola entre dois anos observados (não extrapola): municípios criados
    durante o período continuam sem população antes da criação.
    Devolve cod6, ano, populacao, populacao_imputada (bool).
    """
    # O SIDRA chega como texto; to_numeric pode gerar Float64 (anulável) ou object,
    # que a interpolação não aceita. Converte para float64 comum.
    pop = pop.assign(populacao=pd.to_numeric(pop["populacao"], errors="coerce").astype("float64"),
                     ano=pop["ano"].astype("int64"))
    largo = pop.pivot_table(index="cod6", columns="ano", values="populacao", aggfunc="first")
    largo = largo.reindex(columns=anos)
    observado = largo.notna()
    preenchido = largo.T.interpolate(method="index", limit_area="inside").T
    saida = preenchido.stack(future_stack=True).rename("populacao").reset_index()
    saida["populacao_imputada"] = (~observado).stack(future_stack=True).values & saida[
        "populacao"
    ].notna().values
    return saida


# ------------------------------------------------------------------ painel
def montar_painel(
    municipios: pd.DataFrame,
    anos: list[int],
    polos: pd.DataFrame,
    internacoes: pd.DataFrame,
    populacao: pd.DataFrame,
) -> pd.DataFrame:
    """Painel município × ano com polos, internações por grupo e população.

    - `municipios`: cod6, cod_ibge7, uf, regiao.
    - `polos`: cod6, ano, n_polos (só municípios com polo).
    - `internacoes`: cod6, ano, grupo, internacoes (já filtrado por tipo de AIH).
    - `populacao`: cod6, ano, populacao, populacao_imputada.
    Contagens ausentes viram 0; população ausente fica NaN.
    """
    chave = pd.MultiIndex.from_product(
        [municipios["cod6"].astype("string"), anos], names=["cod6", "ano"]
    ).to_frame(index=False)
    chave["ano"] = chave["ano"].astype("int64")
    painel = chave.merge(municipios, on="cod6", how="left")

    polos = polos.assign(ano=polos["ano"].astype("int64"))
    painel = painel.merge(polos[["cod6", "ano", "n_polos"]], on=["cod6", "ano"], how="left")
    painel["n_polos"] = painel["n_polos"].fillna(0).astype("int64")

    largo = internacoes.assign(ano=internacoes["ano"].astype("int64")).pivot_table(
        index=["cod6", "ano"], columns="grupo", values="internacoes", aggfunc="sum"
    )
    # Todas as colunas de grupo existem, mesmo que um grupo não ocorra no recorte.
    largo = largo.reindex(columns=[*GRUPOS_CID, GRUPO_OUTRAS])
    largo.columns = [f"int_{c}" for c in largo.columns]
    painel = painel.merge(largo.reset_index(), on=["cod6", "ano"], how="left")
    for c in [c for c in painel.columns if c.startswith("int_")]:
        painel[c] = painel[c].fillna(0).astype("int64")

    populacao = populacao.assign(ano=populacao["ano"].astype("int64"))
    painel = painel.merge(populacao, on=["cod6", "ano"], how="left")
    return painel.sort_values(["cod6", "ano"]).reset_index(drop=True)


def codigos_incentivo_por_tipo(inc: pd.DataFrame, st: pd.DataFrame, competencia: int,
                               col_codigo: str = "SGRUPHAB") -> pd.DataFrame:
    """Para cada código de habilitação/incentivo vigente na competência, conta os
    estabelecimentos que o têm e quantos deles são polos tipo 74 (CNES-ST).

    Serve para identificar, pelos dados, os códigos ligados ao Programa
    Academia da Saúde. Devolve: codigo, n_estab, n_estab_tipo74.
    """
    inc = inc.copy()
    inc["codigo"] = inc[col_codigo].astype("string").str.strip()
    if {"CMPT_INI", "CMPT_FIM"} <= set(inc.columns):
        ini, fim = _competencia(inc["CMPT_INI"]), _competencia(inc["CMPT_FIM"])
        inc = inc.loc[((ini.isna() | (ini <= competencia)) & (fim.isna() | (fim >= competencia))).values]
    tipo = st[["CNES", "TP_UNID"]].drop_duplicates("CNES")
    tipo = tipo.assign(polo=tipo["TP_UNID"].astype("string").str.strip().str.zfill(2) == TP_UNID_POLO)
    base = inc[["CNES", "codigo"]].drop_duplicates().merge(tipo[["CNES", "polo"]], on="CNES", how="left")
    base["polo"] = base["polo"].fillna(False).astype(bool)
    return (base.groupby("codigo")
                .agg(n_estab=("CNES", "nunique"), n_estab_tipo74=("polo", "sum"))
                .reset_index())
