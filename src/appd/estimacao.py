"""Funções de estimação reutilizadas no caderno 02.

Ficam aqui apenas operações genéricas e repetidas (balanceamento, bootstrap,
tabela-síntese e MDE). As especificações dos modelos ficam no caderno, onde
cada escolha é justificada em markdown.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats

from appd import SEMENTE


def smd(x_trat: pd.Series, x_ctrl: pd.Series, w_trat=None, w_ctrl=None) -> float:
    """Diferença média padronizada (desvio-padrão combinado sem pesos)."""
    m1 = np.average(x_trat, weights=w_trat)
    m0 = np.average(x_ctrl, weights=w_ctrl)
    dp = np.sqrt((np.var(x_trat, ddof=1) + np.var(x_ctrl, ddof=1)) / 2)
    return float((m1 - m0) / dp) if dp > 0 else 0.0


def tabela_balanceamento(
    dados: pd.DataFrame,
    covariaveis: list[str],
    col_trat: str,
    pesos: pd.Series | None = None,
) -> pd.DataFrame:
    """Médias por grupo e SMD de cada covariável (com ou sem pesos)."""
    t = dados[col_trat] == 1
    w = pesos if pesos is not None else pd.Series(1.0, index=dados.index)
    linhas = []
    for c in covariaveis:
        linhas.append(
            {
                "covariavel": c,
                "media_tratados": np.average(dados.loc[t, c], weights=w[t]),
                "media_controles": np.average(dados.loc[~t, c], weights=w[~t]),
                "smd": smd(dados.loc[t, c], dados.loc[~t, c], w[t], w[~t]),
            }
        )
    return pd.DataFrame(linhas)


def bootstrap(
    dados: pd.DataFrame,
    estimador: Callable[[pd.DataFrame], float],
    n_reps: int = 1000,
    semente: int = SEMENTE,
    alpha: float = 0.05,
) -> dict:
    """Bootstrap não paramétrico (reamostragem de linhas) com IC por percentil."""
    rng = np.random.default_rng(semente)
    n = len(dados)
    estimativas = np.array(
        [estimador(dados.iloc[rng.integers(0, n, n)]) for _ in range(n_reps)]
    )
    return {
        "estimativa": estimador(dados),
        "ep": float(np.std(estimativas, ddof=1)),
        "ic_inf": float(np.quantile(estimativas, alpha / 2)),
        "ic_sup": float(np.quantile(estimativas, 1 - alpha / 2)),
        "n_reps": n_reps,
    }


SINTESE: list[dict] = []


def registrar(metodo: str, estimativa: float, ep: float, ic_inf: float,
              ic_sup: float, n: int, nota: str = "") -> None:
    """Acrescenta uma linha à tabela-síntese (tab08_sintese)."""
    SINTESE.append(
        {"metodo": metodo, "estimativa": estimativa, "ep": ep,
         "ic95_inf": ic_inf, "ic95_sup": ic_sup, "n": n, "nota": nota}
    )


def tabela_sintese() -> pd.DataFrame:
    return pd.DataFrame(SINTESE)


def mde(ep: float, alpha: float = 0.05, poder: float = 0.80) -> float:
    """Efeito mínimo detectável (bicaudal): (z_{1-α/2} + z_{poder}) × EP."""
    return float((stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(poder)) * ep)
