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


def configurar_cache(raiz: Path) -> Path:
    """Aponta o cache do PySUS para data/raw/pysus (vazio na entrega)."""
    import pysus

    destino = Path(raiz) / "data" / "raw" / "pysus"
    destino.mkdir(parents=True, exist_ok=True)
    return pysus.set_cache(destino)


def _ler_parquets(caminhos: list[str], colunas: list[str] | None) -> pd.DataFrame:
    """Lê os parquets baixados pelo PySUS, só com as colunas pedidas, como texto."""
    partes = []
    for caminho in caminhos:
        try:
            parte = pd.read_parquet(caminho, columns=colunas)
        except (KeyError, ValueError):
            # Coluna ausente no layout desse ano: lê tudo e mantém a interseção.
            parte = pd.read_parquet(caminho)
            if colunas is not None:
                parte = parte[[c for c in colunas if c in parte.columns]]
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
    import pysus

    funcao = getattr(pysus.ftp, sistema)
    argumentos = {"state": uf, "year": ano, "group": grupo, "show_progress": False}
    if mes is not None:
        argumentos["month"] = mes

    ultimo_erro: Exception | None = None
    for origem in ("origin", "catalog"):
        try:
            caminhos = funcao(**argumentos, source=origem)
            caminhos = [caminhos] if isinstance(caminhos, (str, Path)) else list(caminhos)
            df = _ler_parquets(caminhos, colunas)
            if apagar_bruto:
                apagar(caminhos)
            _registrar(
                f"{sistema.upper()}-{grupo or ''}",
                {"uf": uf, "ano": ano, "mes": mes},
                "FTP DATASUS" if origem == "origin" else "catálogo PySUS (espelho)",
                len(df),
            )
            return df
        except Exception as erro:  # noqa: BLE001 - registra e tenta a próxima origem
            ultimo_erro = erro
    raise RuntimeError(
        f"Falha ao baixar {sistema.upper()}-{grupo} {uf} {ano}/{mes}: {ultimo_erro}"
    ) from ultimo_erro


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
) -> pd.DataFrame:
    """Consulta uma tabela do SIDRA no nível municipal (N6) via sidrapy.

    Devolve as colunas originais do SIDRA, como texto, sem a linha de cabeçalho.
    O número da tabela e da variável deve ser verificado na Fase 0 (PLANO.md,
    seção 5).
    """
    import sidrapy

    df = sidrapy.get_table(
        table_code=tabela,
        territorial_level="6",
        ibge_territorial_code="all",
        variable=variavel,
        period=periodos,
        classifications=classificacoes,
    )
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True).astype("string")
    _registrar(
        f"SIDRA-{tabela}",
        {"variavel": variavel, "periodos": periodos, "classificacoes": classificacoes},
        "API SIDRA/IBGE",
        len(df),
    )
    return df
