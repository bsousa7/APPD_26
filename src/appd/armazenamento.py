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
