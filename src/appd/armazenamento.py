"""Armazenamento persistente e retomada da extração.

- No Google Colab, `data/processed/` passa a apontar (link simbólico) para uma
  pasta do Google Drive, para que os resultados sobrevivam ao fim da sessão.
  Fora do Colab, nada muda: os arquivos ficam no próprio repositório.
- `com_checkpoint` grava cada parte da extração assim que termina; numa nova
  execução, a parte já gravada é lida do disco em vez de baixada de novo.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

PASTA_DRIVE = "APPD_26_dados"


def no_colab() -> bool:
    return "google.colab" in sys.modules


def preparar_armazenamento(raiz: Path, pasta_drive: str = PASTA_DRIVE) -> Path:
    """Garante `data/processed/`; no Colab, liga essa pasta ao Google Drive.

    Devolve sempre o caminho relativo `raiz/data/processed`, que é o único
    usado pelo resto do código.
    """
    local = Path(raiz) / "data" / "processed"
    if not no_colab():
        local.mkdir(parents=True, exist_ok=True)
        return local

    from google.colab import drive  # disponível só no Colab

    drive.mount("/content/drive")
    destino = Path("/content/drive/MyDrive") / pasta_drive / "processed"
    destino.mkdir(parents=True, exist_ok=True)
    if local.is_symlink():
        print(f"Dados processados no Google Drive: MyDrive/{pasta_drive}/processed")
        return local
    if local.exists():
        # Na cópia clonada há apenas arquivos .gitkeep: podem ser removidos.
        conteudo = [p for p in local.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        if conteudo:
            raise RuntimeError(
                f"{local} já tem arquivos; mova-os para o Drive antes de continuar."
            )
        shutil.rmtree(local)
    local.symlink_to(destino, target_is_directory=True)
    n = sum(1 for _ in destino.rglob("*.parquet"))
    print(f"Dados processados no Google Drive: MyDrive/{pasta_drive}/processed "
          f"({n} arquivos .parquet já existentes)")
    return local


def com_checkpoint(arquivo: Path, gerar: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """Lê `arquivo` se ele existir; senão chama `gerar()`, grava e devolve.

    A gravação é atômica (arquivo temporário + renomeação), para que uma queda
    no meio da escrita não deixe um checkpoint corrompido.
    """
    arquivo = Path(arquivo)
    if arquivo.exists():
        return pd.read_parquet(arquivo)
    df = gerar()
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_suffix(".tmp")
    df.to_parquet(temporario, index=False)
    os.replace(temporario, arquivo)
    return df


def extrair_partes(
    nome: str,
    chaves: list[tuple],
    arquivo: Callable[..., Path],
    gerar: Callable[..., pd.DataFrame],
    falhas: list[dict],
    simultaneos: int = 3,
    tentativas: int = 3,
    espera_s: float = 10.0,
    relatar_a_cada: int = 25,
) -> pd.DataFrame:
    """Executa `gerar(*chave)` para cada chave, com checkpoint em `arquivo(*chave)`.

    - Até `simultaneos` partes rodam ao mesmo tempo (threads); como as chaves
      vêm ordenadas por ano e UF, na prática são UFs diferentes em paralelo.
    - Cada parte tem até `tentativas` tentativas, com espera crescente
      (`espera_s`, 2×`espera_s`, ...), para falhas passageiras do FTP ou do
      banco de estado do PySUS ("database is locked").
    - Partes já gravadas são lidas do disco. Uma parte que falha em todas as
      tentativas é registrada em `falhas` e não interrompe as demais; na
      próxima execução, só ela é refeita.
    Devolve a concatenação das partes não vazias.
    """
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _uma(chave):
        ultimo = None
        for t in range(1, tentativas + 1):
            try:
                return com_checkpoint(arquivo(*chave), lambda: gerar(*chave))
            except Exception as erro:  # noqa: BLE001 - tenta de novo e depois registra
                ultimo = erro
                if t < tentativas:
                    time.sleep(espera_s * t)
        raise ultimo

    ja_gravadas = sum(Path(arquivo(*chave)).exists() for chave in chaves)
    print(f"{nome}: {ja_gravadas} de {len(chaves)} partes já gravadas (lidas do disco); "
          f"{len(chaves) - ja_gravadas} a baixar", flush=True)
    partes, t0, n_falhas = [], time.time(), len(falhas)
    with ThreadPoolExecutor(max_workers=max(1, simultaneos)) as executor:
        futuros = {executor.submit(_uma, chave): chave for chave in chaves}
        for i, futuro in enumerate(as_completed(futuros), 1):
            chave = futuros[futuro]
            try:
                partes.append(futuro.result())
            except Exception as erro:  # noqa: BLE001
                if len(falhas) == n_falhas:  # mostra a primeira falha de cada base
                    print(f"{nome}: falha em {chave}: {str(erro)[:300]}")
                falhas.append({"base": nome, "parte": str(chave), "erro": str(erro)[:300]})
            if i % relatar_a_cada == 0 or i == len(chaves):
                print(f"{nome}: {i}/{len(chaves)} partes | {(time.time() - t0) / 60:.1f} min "
                      f"| falhas: {len(falhas) - n_falhas}", flush=True)
    partes = [p for p in partes if len(p)]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def preparar_saidas(raiz: Path, pasta_drive: str = PASTA_DRIVE) -> Path:
    """Garante `outputs/` (figuras e tabelas); no Colab, liga essa pasta ao Drive.

    Arquivos que já existam na cópia local (ex.: fig01_dag.png gerada na seção 1)
    são copiados para o Drive antes da ligação, sem sobrescrever os de lá.
    Devolve sempre o caminho relativo `raiz/outputs`.
    """
    local = Path(raiz) / "outputs"
    if not no_colab():
        for sub in ("figuras", "tabelas"):
            (local / sub).mkdir(parents=True, exist_ok=True)
        return local
    if local.is_symlink():
        return local
    from google.colab import drive  # disponível só no Colab

    drive.mount("/content/drive")
    destino = Path("/content/drive/MyDrive") / pasta_drive / "outputs"
    for sub in ("figuras", "tabelas"):
        (destino / sub).mkdir(parents=True, exist_ok=True)
    if local.exists():
        for arquivo in local.rglob("*"):
            if arquivo.is_file() and arquivo.name != ".gitkeep":
                alvo = destino / arquivo.relative_to(local)
                if not alvo.exists():
                    alvo.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(arquivo, alvo)
        shutil.rmtree(local)
    local.symlink_to(destino, target_is_directory=True)
    print(f"Figuras e tabelas no Google Drive: MyDrive/{pasta_drive}/outputs")
    return local
