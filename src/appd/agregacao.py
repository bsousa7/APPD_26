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

# Código do tipo de estabelecimento "Polo Academia da Saúde" no CNES
# (Portaria SAS/MS nº 24/2014).
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


def agregar_sih(
    rd: pd.DataFrame,
    col_mun: str = "MUNIC_RES",
    col_ano: str = "ANO_CMPT",
    col_cid: str = "DIAG_PRINC",
) -> pd.DataFrame:
    """Conta internações por município de residência × ano × grupo de CID.

    Linhas cujo diagnóstico principal não pertence a nenhum grupo são
    descartadas. Devolve colunas: cod6, ano, grupo, internacoes.
    """
    base = pd.DataFrame(
        {
            "cod6": normalizar_cod6(rd[col_mun]),
            "ano": pd.to_numeric(rd[col_ano], errors="coerce").astype("Int64"),
            "grupo": classificar_cid(rd[col_cid]),
        }
    )
    base = base.dropna(subset=["grupo", "ano", "cod6"])
    return (
        base.groupby(["cod6", "ano", "grupo"], observed=True)
        .size()
        .rename("internacoes")
        .reset_index()
    )


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
