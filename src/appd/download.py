"""Download das fontes originais.

- DATASUS (CNES, SIH, SIM) via PySUS 2.x (`pysus.ftp.*`). Por padrão lê do FTP
  do DATASUS (`source="origin"`). Se o FTP falhar, tenta o espelho/catálogo do
  próprio PySUS (`source="catalog"`) e registra a troca, conforme o PLANO.md,
  seção 5 ("Se o FTP do DATASUS falhar").
- IBGE: API de localidades (lista de municípios) e SIDRA via `sidrapy`.

Cada chamada é registrada em REGISTRO_ACESSOS (fonte, parâmetros, origem
efetiva e data/hora), para documentar no caderno a data de acesso.
"""

from __future__ import annotations

import datetime as dt
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

URL_MUNICIPIOS_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

REGISTRO_ACESSOS: list[dict] = []


def _registrar(fonte: str, parametros: dict, origem: str, n_linhas: int | None) -> None:
    REGISTRO_ACESSOS.append(
        {
            "fonte": fonte,
            "parametros": parametros,
            "origem_efetiva": origem,
            "linhas": n_linhas,
            "acesso_em": dt.datetime.now().isoformat(timespec="seconds"),
        }
    )


def registro_acessos() -> pd.DataFrame:
    """Tabela com todas as chamadas feitas na sessão (para o markdown do caderno)."""
    return pd.DataFrame(REGISTRO_ACESSOS)


CACHE_DIR: Path | None = None


def configurar_cache(raiz: Path) -> Path:
    """Aponta o cache do PySUS para data/raw/pysus (vazio na entrega).

    O PySUS fixa a pasta de cache no momento da importação; por isso a variável
    de ambiente é definida antes do primeiro `import pysus`. Se o PySUS já tiver
    sido importado, os arquivos podem ir para ~/pysus, e `_resolver` os acha lá.
    """
    import os
    import sys

    global CACHE_DIR
    destino = (Path(raiz) / "data" / "raw" / "pysus").resolve()
    destino.mkdir(parents=True, exist_ok=True)
    if "pysus" not in sys.modules:
        os.environ["PYSUS_CACHEPATH"] = str(destino)
    import pysus

    pysus.set_cache(destino)
    CACHE_DIR = destino
    return destino


def _pastas_de_cache() -> list[Path]:
    pastas = [CACHE_DIR, Path.home() / "pysus", Path.cwd()]
    try:
        import pysus

        pastas.append(Path(pysus.CACHEPATH))
    except ImportError:
        pass
    vistas, saida = set(), []
    for p in pastas:
        if p is not None and p.exists() and p.resolve() not in vistas:
            vistas.add(p.resolve())
            saida.append(p)
    return saida


def _resolver(caminho: str) -> Path:
    """Caminho local do arquivo baixado pelo PySUS.

    O PySUS às vezes devolve só o nome do arquivo (ex.: "INAC1512.parquet");
    nesse caso, procura-o pelo nome nas pastas de cache (o mais recente).
    """
    p = Path(caminho)
    if p.exists():
        return p
    achados = [a for pasta in _pastas_de_cache() for a in pasta.rglob(p.name)]
    if not achados:
        raise FileNotFoundError(
            f"{caminho}: não encontrado nas pastas de cache {[str(x) for x in _pastas_de_cache()]}")
    return max(achados, key=lambda a: a.stat().st_mtime)


def _fora_do_laco_jupyter(funcao, **argumentos):
    """Executa uma chamada do PySUS numa thread separada.

    Dentro do Jupyter já existe um laço de eventos ativo; nesse caso o PySUS
    aplica o `nest_asyncio`, que é incompatível com o ipykernel no Python 3.13
    (erros "cannot enter context ... is already entered"). Numa thread nova
    não há laço ativo e o PySUS usa `asyncio.run` normalmente.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(funcao, **argumentos).result()


def _colunas_disponiveis(caminho: str) -> list[str]:
    """Nomes das colunas de um parquet (arquivo ou pasta) sem ler os valores."""
    import pyarrow.dataset as ds

    return list(ds.dataset(caminho, format="parquet").schema.names)


def _ler_parquets(caminhos: list[str], colunas: list[str] | None) -> pd.DataFrame:
    """Lê os parquets baixados pelo PySUS, só com as colunas pedidas, como texto.

    Se alguma coluna pedida não existir no layout daquele ano, lê apenas as que
    existem (nunca o arquivo inteiro, que pode conter CPF/CNPJ).
    """
    partes = []
    for caminho in caminhos:
        if colunas is None:
            parte = pd.read_parquet(caminho)
        else:
            existentes = [c for c in colunas if c in _colunas_disponiveis(caminho)]
            parte = pd.read_parquet(caminho, columns=existentes)
        partes.append(parte.astype("string"))
    if not partes:
        return pd.DataFrame(columns=colunas or [], dtype="string")
    return pd.concat(partes, ignore_index=True)


def apagar(caminhos: list[str]) -> None:
    """Apaga os arquivos brutos depois de agregados (PLANO.md, seção 5)."""
    for caminho in caminhos:
        p = Path(caminho)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists():
            p.unlink()
        for irmao in (p.with_suffix(".dbc"), p.with_suffix(".dbf"), p.with_suffix(".DBC")):
            if irmao.exists() and irmao.is_file():
                irmao.unlink()


def _baixar_caminhos(sistema: str, uf: str, ano: int, mes: int | None,
                     grupo: str | None) -> tuple[list[str], str]:
    """Baixa o arquivo pelo PySUS: FTP do DATASUS e, se falhar, o catálogo.

    Devolve (caminhos dos parquets, origem efetiva). Lista vazia conta como
    falha (arquivo inexistente naquela origem).
    """
    import pysus

    funcao = getattr(pysus.ftp, sistema)
    argumentos = {"state": uf, "year": ano, "group": grupo, "show_progress": False}
    if mes is not None:
        argumentos["month"] = mes

    erros = []
    for origem in ("origin", "catalog"):
        try:
            caminhos = _fora_do_laco_jupyter(funcao, **argumentos, source=origem)
            caminhos = [caminhos] if isinstance(caminhos, (str, Path)) else list(caminhos)
            if not caminhos:
                raise FileNotFoundError("nenhum arquivo encontrado")
            return [str(_resolver(str(c))) for c in caminhos], (
                "FTP DATASUS" if origem == "origin" else "catálogo PySUS (espelho)"
            )
        except Exception as erro:  # noqa: BLE001 - registra e tenta a próxima origem
            erros.append(f"{origem}: {erro}")
    raise RuntimeError(
        f"Falha ao baixar {sistema.upper()}-{grupo} {uf} {ano}/{mes}: " + " | ".join(erros)
    )


def baixar_datasus(
    sistema: str,
    uf: str,
    ano: int,
    mes: int | None = None,
    grupo: str | None = None,
    colunas: list[str] | None = None,
    apagar_bruto: bool = True,
) -> pd.DataFrame:
    """Baixa um arquivo do DATASUS via PySUS e devolve um DataFrame de texto.

    sistema: "cnes", "sih" ou "sim". grupo: "ST", "IN", "EP", "LT" (CNES) ou
    "RD" (SIH). Tenta primeiro o FTP do DATASUS e, se falhar, o catálogo do
    PySUS; a origem efetiva fica em REGISTRO_ACESSOS.
    """
    caminhos, origem = _baixar_caminhos(sistema, uf, ano, mes, grupo)
    try:
        df = _ler_parquets(caminhos, colunas)
    finally:
        if apagar_bruto:
            apagar(caminhos)
    _registrar(f"{sistema.upper()}-{grupo or ''}", {"uf": uf, "ano": ano, "mes": mes},
               origem, len(df))
    return df


def esquema_datasus(sistema: str, uf: str, ano: int, mes: int | None = None,
                    grupo: str | None = None) -> pd.DataFrame:
    """Nomes e tipos das colunas de um arquivo do DATASUS, sem ler os valores.

    Usado para os dicionários de variáveis (etapa 5 das orientações): descreve o
    arquivo bruto antes de qualquer transformação. O bruto é apagado em seguida.
    """
    import pyarrow.dataset as ds

    caminhos, origem = _baixar_caminhos(sistema, uf, ano, mes, grupo)
    try:
        esquema = ds.dataset(caminhos[0], format="parquet").schema
        saida = pd.DataFrame({"coluna": esquema.names,
                              "tipo_no_arquivo": [str(t) for t in esquema.types]})
    finally:
        apagar(caminhos)
    _registrar(f"{sistema.upper()}-{grupo or ''} (esquema)", {"uf": uf, "ano": ano, "mes": mes},
               origem, None)
    return saida


def municipios_ibge(timeout: int = 60) -> pd.DataFrame:
    """Lista oficial de municípios (API de localidades do IBGE).

    Devolve: cod_ibge7, cod6, municipio, uf, regiao (todos texto).
    """
    import requests

    resposta = requests.get(URL_MUNICIPIOS_IBGE, timeout=timeout)
    resposta.raise_for_status()
    linhas = []
    for m in resposta.json():
        uf = (m.get("microrregiao") or {}).get("mesorregiao", {}).get("UF") or (
            m.get("regiao-imediata") or {}
        ).get("regiao-intermediaria", {}).get("UF")
        linhas.append(
            {
                "cod_ibge7": str(m["id"]),
                "municipio": m["nome"],
                "uf": uf["sigla"],
                "regiao": uf["regiao"]["nome"],
            }
        )
    df = pd.DataFrame(linhas).astype("string")
    df["cod6"] = df["cod_ibge7"].str[:6]
    _registrar("IBGE-localidades", {"url": URL_MUNICIPIOS_IBGE}, "API IBGE", len(df))
    return df[["cod_ibge7", "cod6", "municipio", "uf", "regiao"]]


def tabela_sidra(
    tabela: str,
    variavel: str,
    periodos: str,
    classificacoes: dict[str, str] | None = None,
    nivel: str = "6",
    territorio: str = "all",
) -> pd.DataFrame:
    """Consulta uma tabela do SIDRA no nível municipal (N6) via sidrapy.

    Devolve as colunas originais do SIDRA, como texto, sem a linha de cabeçalho.
    `territorio` aceita, por exemplo, "all" ou "in n3 12" (municípios do AC).
    A API do SIDRA limita cada consulta a 50 mil valores.
    O número da tabela e da variável deve ser verificado na Fase 0 (PLANO.md,
    seção 5).
    """
    import sidrapy

    df = sidrapy.get_table(
        table_code=tabela,
        territorial_level=nivel,
        ibge_territorial_code=territorio,
        variable=variavel,
        period=periodos,
        classifications=classificacoes,
    )
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True).astype("string")
    _registrar(
        f"SIDRA-{tabela}",
        {"variavel": variavel, "periodos": periodos, "classificacoes": classificacoes,
         "nivel": nivel, "territorio": territorio},
        "API SIDRA/IBGE",
        len(df),
    )
    return df


URL_METADADOS_SIDRA = "https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados"


def metadados_sidra(tabela: str, timeout: int = 60) -> dict:
    """Metadados de uma tabela do SIDRA (variáveis, classificações e categorias)."""
    import requests

    url = URL_METADADOS_SIDRA.format(tabela=tabela)
    resposta = requests.get(url, timeout=timeout)
    resposta.raise_for_status()
    _registrar(f"SIDRA-{tabela} (metadados)", {"url": url}, "API agregados/IBGE", None)
    return resposta.json()


def _idade_inicial(nome: str) -> tuple[int | None, bool]:
    """'45 anos' -> (45, False); '100 anos ou mais' -> (100, True); outros -> (None, False)."""
    import re

    m = re.fullmatch(r"(\d+) anos?( ou mais)?", nome.strip())
    if not m:
        return None, False
    return int(m.group(1)), m.group(2) is not None


def populacao_idosos_sidra(
    tabela: str,
    variavel: str,
    periodo: str,
    codigos_uf: list[str],
    idade_minima: int = 60,
) -> pd.DataFrame:
    """População total e de `idade_minima`+ anos por município, de uma tabela do Censo.

    Usa os metadados da tabela para achar a classificação de idade e as
    categorias de idade simples ("N anos" e a última "N anos ou mais"). Antes de
    consultar os municípios, confere no nível Brasil que a soma das idades
    simples bate com o total (diferença < 0,5%); se não bater, as categorias
    não são idades simples e a função para com erro.
    As consultas são feitas por UF, por causa do limite de 50 mil valores.
    Devolve: cod_ibge7, pop_total_censo, pop_idosos.
    """
    meta = metadados_sidra(tabela)
    classif = [c for c in meta["classificacoes"] if "idade" in c["nome"].lower()]
    if len(classif) != 1:
        raise ValueError(f"Tabela {tabela}: esperada 1 classificação de idade, "
                         f"achadas {[c['nome'] for c in meta['classificacoes']]}")
    classif = classif[0]
    cats = pd.DataFrame(classif["categorias"])
    cats["nome"] = cats["nome"].astype(str)
    idade = cats["nome"].map(_idade_inicial)
    cats["idade"] = [i for i, _ in idade]
    cats["aberta"] = [a for _, a in idade]
    total_id = cats.loc[cats["nome"].str.strip() == "Total", "id"]
    if len(total_id) != 1:
        raise ValueError(f"Tabela {tabela}: categoria 'Total' de idade não encontrada.")
    total_id = str(total_id.iloc[0])
    abertas = cats.loc[cats["aberta"]]
    topo = abertas.loc[abertas["idade"] == abertas["idade"].max()]
    simples = pd.concat([cats.loc[cats["idade"].notna() & ~cats["aberta"]], topo])
    menos_de_1 = cats.loc[cats["nome"].str.lower().str.startswith("menos de 1")]
    cid = str(classif["id"])

    def _valores(df: pd.DataFrame) -> pd.Series:
        return pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

    # Conferência no nível Brasil: idades simples (+ menos de 1 ano) somam o total?
    ids_todas = ",".join(map(str, pd.concat([simples, menos_de_1])["id"])) + "," + total_id
    br = tabela_sidra(tabela, variavel, periodo, {cid: ids_todas}, nivel="1", territorio="all")
    nome_col = classif["nome"]
    eh_total = br[nome_col].str.strip() == "Total"
    soma, total = _valores(br.loc[~eh_total]).sum(), _valores(br.loc[eh_total]).sum()
    if total == 0 or abs(soma - total) / total > 0.005:
        raise ValueError(f"Tabela {tabela}: idades simples somam {soma:,.0f}, total {total:,.0f}.")

    ids_idosos = simples.loc[simples["idade"] >= idade_minima, "id"].astype(str)
    consulta = {cid: ",".join(ids_idosos) + "," + total_id}
    partes = []
    for uf in codigos_uf:
        partes.append(tabela_sidra(tabela, variavel, periodo, consulta,
                                   nivel="6", territorio=f"in n3 {uf}"))
    dados = pd.concat(partes, ignore_index=True)
    dados["valor"] = _valores(dados)
    eh_total = dados[nome_col].str.strip() == "Total"
    saida = pd.DataFrame({
        "pop_total_censo": dados.loc[eh_total].groupby("Município (Código)")["valor"].sum(),
        "pop_idosos": dados.loc[~eh_total].groupby("Município (Código)")["valor"].sum(),
    }).reset_index().rename(columns={"Município (Código)": "cod_ibge7"})
    saida["cod_ibge7"] = saida["cod_ibge7"].astype("string")
    return saida


URL_PERIODOS_SIDRA = "https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos"


def periodos_sidra(tabela: str, timeout: int = 60) -> list[str]:
    """Lista oficial de períodos disponíveis numa tabela do SIDRA (ex.: anos)."""
    import requests

    url = URL_PERIODOS_SIDRA.format(tabela=tabela)
    resposta = requests.get(url, timeout=timeout)
    resposta.raise_for_status()
    _registrar(f"SIDRA-{tabela} (períodos)", {"url": url}, "API agregados/IBGE", None)
    return [str(p["id"]) for p in resposta.json()]
