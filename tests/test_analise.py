"""Testes da base analítica (painel fictício mínimo, só para verificar a lógica)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from appd.analise import (  # noqa: E402
    calcular_taxas,
    definir_tratamento,
    grupo_de_coorte,
    montar_base_psm,
    selecionar_amostra_did,
    tabela_descritiva,
)

ANOS = list(range(2008, 2020))
# a: polo em 2011 (sai: antes de 2013) | b: polo em 2014, perde em 2017
# c: nunca tratado | d: instalado em 2013 (sem população antes) | e: polo em 2013
POLOS = {"a": {2011: 1}, "b": {2014: 1, 2015: 1, 2016: 1}, "c": {}, "d": {}, "e": {2013: 2}}


def _painel():
    linhas = []
    for cod, polos in POLOS.items():
        for ano in ANOS:
            n = polos.get(ano, 0)
            if cod in ("a", "e") and ano > min(polos):
                n = max(polos.values())
            linhas.append({
                "cod6": cod, "ano": ano, "uf": "AC", "regiao": "Norte", "n_polos": n,
                "int_hipertensao": 1, "int_avc": 2, "int_diabetes": 3, "int_apendicite": 1,
                "int_outras": 10,
                "populacao": np.nan if (cod == "d" and ano < 2013) else 10_000.0,
            })
    return pd.DataFrame(linhas)


def test_taxas():
    p = calcular_taxas(_painel())
    linha = p.iloc[0]
    assert linha["int_cv_dm"] == 6
    assert np.isclose(linha["taxa_cv_dm"], 6.0)  # 6 / 10.000 × 10.000
    assert np.isclose(linha["taxa_apendicite"], 1.0)


def test_tratamento_absorvente_e_polo_perdido():
    p = definir_tratamento(_painel(), absorvente=True).set_index(["cod6", "ano"])
    assert p.loc[("b", 2013), "D"] == 0 and p.loc[("b", 2014), "D"] == 1
    assert p.loc[("b", 2018), "D"] == 1          # absorvente: continua tratado
    assert bool(p.loc[("b", 2018), "perdeu_polo"])
    assert p.loc[("c", 2019), "g"] == 0 and not bool(p.loc[("e", 2019), "perdeu_polo"])
    q = definir_tratamento(_painel(), absorvente=False).set_index(["cod6", "ano"])
    assert q.loc[("b", 2018), "D"] == 0          # não absorvente: segue o CNES


def test_amostra_did_e_registro():
    p = calcular_taxas(definir_tratamento(_painel()))
    did, reg = selecionar_amostra_did(p, 2013)
    assert set(did["cod6"]) == {"b", "c", "e"}
    assert reg["excluidos"].tolist() == [0, 1, 1]
    assert reg["restantes"].iloc[-1] == 3


def test_base_psm_e_descritiva():
    p = calcular_taxas(definir_tratamento(_painel()))
    did, _ = selecionar_amostra_did(p, 2013)
    cov = pd.DataFrame({"cod6": ["b", "c", "e"], "pop_total_censo": [10_000.0] * 3,
                        "pib_per_capita": [5000.0, 6000.0, 7000.0], "pct_60_mais": [10.0, 12.0, 11.0],
                        "leitos_sus_por_mil": [1.0, 2.0, 0.5],
                        "equipes_tipo_01": [2, 1, 0], "equipes_tipo_02": [1, 1, 1]})
    base = montar_base_psm(did, cov, coortes_tratadas=(2013, 2015), janela_pos=(2016, 2018))
    assert set(base["cod6"]) == {"b", "c", "e"} and base["tratado"].sum() == 2
    assert np.allclose(base["equipes_aps_por_10mil"], [3.0, 2.0, 1.0])
    so01 = montar_base_psm(did, cov, tipos_equipe_aps=["01"])
    assert np.allclose(so01["equipes_aps_por_10mil"], [2.0, 1.0, 0.0])
    assert np.allclose(base["delta_taxa"], 0.0)  # taxas constantes no painel fictício
    tab = tabela_descritiva(base, {"pct_60_mais": "% 60+"})
    assert tab.iloc[0]["media_tratados"] == 10.5 and tab.iloc[-1]["media_tratados"] == 2


def test_grupo_de_coorte():
    g = pd.Series([0, 2013, 2015, 2017, 2022])
    assert grupo_de_coorte(g).tolist() == ["Nunca tratados", "2013", "2015", "2016–2018", "2019–2024"]
