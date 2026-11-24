"""Base analítica (Fase 4): taxas, tratamento, amostras e descritiva.

As escolhas de desenho entram como parâmetros, para que os autores possam
ajustá-las sem mexer no código (docs/decisoes.md):
- `ano_primeira_coorte`: municípios com polo antes dele saem da amostra;
- `absorvente`: D = 1 a partir do primeiro polo, mesmo que o polo deixe de
  existir no CNES (leitura de intenção de tratar);
- `tipos_equipe_aps`: códigos de TIPO_EQP que contam como atenção básica
  (None = todos os tipos, provisório até a conferência dos rótulos).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GRUPOS_DESFECHO = ("hipertensao", "avc", "diabetes")
GRUPO_PLACEBO = "apendicite"
POR_HABITANTES = 10_000


# ------------------------------------------------------------------ taxas
def calcular_taxas(painel: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta o desfecho principal e as taxas por 10 mil habitantes.

    - int_cv_dm: soma das internações por hipertensão, AVC e diabetes;
    - taxa_<grupo>: internações / população × 10.000, para cada grupo,
      para o desfecho principal (taxa_cv_dm) e para o placebo.
    """
    p = painel.copy()
    p["int_cv_dm"] = p[[f"int_{g}" for g in GRUPOS_DESFECHO]].sum(axis=1)
    for g in [*GRUPOS_DESFECHO, GRUPO_PLACEBO, "cv_dm"]:
        p[f"taxa_{g}"] = p[f"int_{g}"] / p["populacao"] * POR_HABITANTES
    return p


# ------------------------------------------------------------- tratamento
def definir_tratamento(painel: pd.DataFrame, absorvente: bool = True) -> pd.DataFrame:
    """Coorte g, indicador de tratamento D e marcador de polo perdido.

    - g: primeiro ano com ao menos um polo tipo 74 (0 = nunca tratado);
    - D: se `absorvente`, 1 a partir de g; senão, 1 só nos anos com polo;
    - perdeu_polo: município tratado que, em algum ano após g, aparece sem polo.
    """
    p = painel.copy()
    com_polo = p.loc[p["n_polos"] > 0]
    g = com_polo.groupby("cod6")["ano"].min()
    p["g"] = p["cod6"].map(g).fillna(0).astype("int64")
    if absorvente:
        p["D"] = ((p["g"] > 0) & (p["ano"] >= p["g"])).astype("int64")
    else:
        p["D"] = (p["n_polos"] > 0).astype("int64")
    sem_polo_depois = (p["g"] > 0) & (p["ano"] > p["g"]) & (p["n_polos"] == 0)
    perdeu = p.loc[sem_polo_depois, "cod6"].unique()
    p["perdeu_polo"] = p["cod6"].isin(perdeu)
    return p


# ---------------------------------------------------------------- amostras
def selecionar_amostra_did(
    painel: pd.DataFrame, ano_primeira_coorte: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica as exclusões da amostra DiD e devolve (painel, registro).

    1. municípios sem população em algum ano (instalados durante o período);
    2. municípios com polo antes de `ano_primeira_coorte` (0 < g < ano).
    O registro traz, para cada passo, municípios excluídos e restantes.
    """
    registro = [{"passo": "Municípios no painel", "excluidos": 0,
                 "restantes": painel["cod6"].nunique()}]
    sem_pop = painel.loc[painel["populacao"].isna(), "cod6"].unique()
    p = painel.loc[~painel["cod6"].isin(sem_pop)]
    registro.append({"passo": "Sem população em algum ano (instalados durante o período)",
                     "excluidos": len(sem_pop), "restantes": p["cod6"].nunique()})
    cedo = p.loc[(p["g"] > 0) & (p["g"] < ano_primeira_coorte), "cod6"].unique()
    p = p.loc[~p["cod6"].isin(cedo)]
    registro.append({"passo": f"Polo antes de {ano_primeira_coorte}",
                     "excluidos": len(cedo), "restantes": p["cod6"].nunique()})
    return p.reset_index(drop=True), pd.DataFrame(registro)


def media_periodo(painel: pd.DataFrame, coluna: str, inicio: int, fim: int) -> pd.Series:
    """Média de `coluna` por município entre `inicio` e `fim` (inclusive)."""
    janela = painel.loc[painel["ano"].between(inicio, fim)]
    return janela.groupby("cod6")[coluna].mean()


def montar_base_psm(
    painel_did: pd.DataFrame,
    covariaveis: pd.DataFrame,
    coortes_tratadas: tuple[int, int] = (2013, 2015),
    janela_pre: tuple[int, int] = (2008, 2010),
    janela_pos: tuple[int, int] = (2016, 2018),
    tipos_equipe_aps: list[str] | None = None,
) -> pd.DataFrame:
    """Base transversal do escore de propensão (PLANO.md, seção 4.4).

    Tratados: g entre `coortes_tratadas`; controles: nunca tratados (g = 0).
    Covariáveis de 2010 + taxa pré (média de taxa_cv_dm na janela pré).
    Desfecho: variação da taxa entre a janela pós e a pré (\"PSM-DiD\").
    """
    unidade = painel_did.drop_duplicates("cod6")[["cod6", "g", "uf", "regiao"]]
    ini, fim = coortes_tratadas
    unidade = unidade.loc[(unidade["g"] == 0) | unidade["g"].between(ini, fim)].copy()
    unidade["tratado"] = (unidade["g"] > 0).astype("int64")

    cov = covariaveis.copy()
    colunas_eq = [c for c in cov.columns if c.startswith("equipes_tipo_")]
    if tipos_equipe_aps is not None:
        colunas_eq = [f"equipes_tipo_{t}" for t in tipos_equipe_aps if f"equipes_tipo_{t}" in cov.columns]
    cov["equipes_aps_por_10mil"] = cov[colunas_eq].sum(axis=1) / cov["pop_total_censo"] * POR_HABITANTES
    cov["log_pop"] = np.log(cov["pop_total_censo"])
    cov["log_pib_per_capita"] = np.log(cov["pib_per_capita"])
    x = cov[["cod6", "pop_total_censo", "pib_per_capita", "log_pop", "log_pib_per_capita",
             "pct_60_mais", "leitos_sus_por_mil", "equipes_aps_por_10mil"]]

    base = unidade.merge(x, on="cod6", how="left")
    pre = media_periodo(painel_did, "taxa_cv_dm", *janela_pre).rename("taxa_pre")
    pos = media_periodo(painel_did, "taxa_cv_dm", *janela_pos).rename("taxa_pos")
    base = base.merge(pre, left_on="cod6", right_index=True, how="left")
    base = base.merge(pos, left_on="cod6", right_index=True, how="left")
    base["delta_taxa"] = base["taxa_pos"] - base["taxa_pre"]
    return base.reset_index(drop=True)


# ---------------------------------------------------------------- descritiva
def tabela_descritiva(base: pd.DataFrame, variaveis: dict[str, str], col_grupo: str = "tratado") -> pd.DataFrame:
    """Média e desvio-padrão por grupo (1 = tratados, 0 = nunca tratados).

    `variaveis` mapeia coluna -> rótulo. Sem leitura causal: só descreve.
    """
    linhas = []
    for col, rotulo in variaveis.items():
        t = base.loc[base[col_grupo] == 1, col]
        c = base.loc[base[col_grupo] == 0, col]
        linhas.append({"variavel": rotulo,
                       "media_tratados": t.mean(), "dp_tratados": t.std(),
                       "media_nunca_tratados": c.mean(), "dp_nunca_tratados": c.std(),
                       "diferenca": t.mean() - c.mean()})
    tab = pd.DataFrame(linhas)
    n = pd.DataFrame([{"variavel": "Municípios (N)",
                       "media_tratados": float((base[col_grupo] == 1).sum()),
                       "media_nunca_tratados": float((base[col_grupo] == 0).sum())}])
    return pd.concat([tab, n], ignore_index=True)


def grupo_de_coorte(g: pd.Series) -> pd.Series:
    """Agrupa coortes para gráficos: 2013, 2014, 2015, 2016–2018, 2019–2024, nunca."""
    def _grupo(v):
        if v == 0:
            return "Nunca tratados"
        if v <= 2015:
            return str(v)
        if v <= 2018:
            return "2016–2018"
        return "2019–2024"
    return g.map(_grupo)
