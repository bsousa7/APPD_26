"""Testes das regras de classificação e agregação (entradas fictícias mínimas)."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from appd.agregacao import (  # noqa: E402
    agregar_sih,
    classificar_cid,
    cod_ibge7_para_cod6,
    contar_polos,
    primeiro_ano_tratamento,
)
from appd.estimacao import mde  # noqa: E402


def test_classificar_cid_limites():
    cid = pd.Series(["I10", "I159", "I16", "I60", "I699", "E10", "E149",
                     "E15", "K35", "K38.0", "K39", "J18", None, "i110"])
    esperado = ["hipertensao", "hipertensao", pd.NA, "avc", "avc", "diabetes",
                "diabetes", pd.NA, "apendicite", "apendicite", pd.NA, pd.NA,
                pd.NA, "hipertensao"]
    obtido = classificar_cid(cid).tolist()
    for o, e in zip(obtido, esperado):
        assert (pd.isna(o) and pd.isna(e)) or o == e


def test_cod6():
    assert cod_ibge7_para_cod6(pd.Series(["5300108"])).tolist() == ["530010"]


def test_agregar_sih():
    rd = pd.DataFrame({"MUNIC_RES": ["530010", "530010", "530010", "120040"],
                       "ANO_CMPT": ["2024", "2024", "2024", "2024"],
                       "DIAG_PRINC": ["I10", "I109", "J180", "E11"]})
    ag = agregar_sih(rd).set_index(["cod6", "grupo"])["internacoes"]
    assert ag[("530010", "hipertensao")] == 2
    assert ag[("120040", "diabetes")] == 1
    assert len(ag) == 2


def test_polos_e_coorte():
    st = pd.DataFrame({"CNES": ["1", "2", "2", "3"],
                       "CODUFMUN": ["530010", "530010", "530010", "120040"],
                       "TP_UNID": ["74", "74", "74", "5"]})
    p = contar_polos(st, 2013)
    assert p.set_index("cod6")["n_polos"].to_dict() == {"530010": 2}
    painel = pd.DataFrame({"cod6": ["a", "a", "b"], "ano": [2012, 2013, 2014],
                           "n_polos": [0, 1, 1]})
    assert primeiro_ano_tratamento(painel).to_dict() == {"a": 2013, "b": 2014}


def test_mde():
    assert abs(mde(1.0) - 2.8016) < 1e-3
