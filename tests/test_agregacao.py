"""Testes das regras de classificação e agregação (entradas fictícias mínimas,
usadas só para verificar a lógica das funções; nenhum dado real)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from appd.agregacao import (  # noqa: E402
    agregar_sih,
    classificar_cid,
    cod_ibge7_para_cod6,
    contar_equipes,
    contar_incentivos,
    contar_polos,
    interpolar_populacao,
    montar_painel,
    primeiro_ano_tratamento,
    somar_leitos,
)
from appd.armazenamento import com_checkpoint  # noqa: E402
from appd.download import _ler_parquets  # noqa: E402
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


def test_agregar_sih_com_outras_e_ident():
    rd = pd.DataFrame({"MUNIC_RES": ["530010"] * 4 + ["120040"],
                       "ANO_CMPT": ["2024"] * 5,
                       "DIAG_PRINC": ["I10", "I109", "J180", "I10", "E11"],
                       "IDENT": ["1", "1", "1", "5", "1"]})
    ag = agregar_sih(rd).set_index(["cod6", "grupo", "ident"])["internacoes"]
    assert ag[("530010", "hipertensao", "1")] == 2
    assert ag[("530010", "hipertensao", "5")] == 1
    assert ag[("530010", "outras", "1")] == 1
    assert ag[("120040", "diabetes", "1")] == 1
    assert ag.sum() == len(rd)  # nenhuma AIH se perde na agregação


def test_polos_e_coorte():
    st = pd.DataFrame({"CNES": ["1", "2", "2", "3"],
                       "CODUFMUN": ["530010", "530010", "530010", "120040"],
                       "TP_UNID": ["74", "74", "74", "5"]})
    p = contar_polos(st, 2013)
    assert p.set_index("cod6")["n_polos"].to_dict() == {"530010": 2}
    painel = pd.DataFrame({"cod6": ["a", "a", "b"], "ano": [2012, 2013, 2014],
                           "n_polos": [0, 1, 1]})
    assert primeiro_ano_tratamento(painel).to_dict() == {"a": 2013, "b": 2014}


def test_incentivos_leitos_equipes():
    inc = pd.DataFrame({"CNES": ["1", "1", "2", "3"], "CODUFMUN": ["120040"] * 4,
                        "INCENTIV": ["81.12", "8113", "8113", "7000"]})
    assert contar_incentivos(inc, 2015, {"81.12", "81.13"}, "INCENTIV")["n_estab_incentivo"].tolist() == [2]
    lt = pd.DataFrame({"CODUFMUN": ["120040", "120040"], "QT_SUS": ["3", "4"],
                       "QT_EXIST": ["5", None]})
    assert somar_leitos(lt).iloc[0][["leitos_sus", "leitos_existentes"]].tolist() == [7, 5]
    ep = pd.DataFrame({"CODUFMUN": ["120040"] * 3, "TIPO_EQP": ["01", "01", "06"],
                       "DT_DESAT": [None, "20100501", ""]})
    eq = contar_equipes(ep).set_index("tipo_eqp")["n_equipes"].to_dict()
    assert eq == {"01": 1, "06": 1}


def test_interpolar_populacao():
    pop = pd.DataFrame({"cod6": ["a", "a", "b"], "ano": [2009, 2011, 2011],
                        "populacao": [100.0, 120.0, 50.0]})
    out = interpolar_populacao(pop, [2009, 2010, 2011]).set_index(["cod6", "ano"])
    assert out.loc[("a", 2010), "populacao"] == 110
    assert bool(out.loc[("a", 2010), "populacao_imputada"])
    assert not bool(out.loc[("a", 2011), "populacao_imputada"])
    assert np.isnan(out.loc[("b", 2009), "populacao"])  # não extrapola


def test_montar_painel():
    mun = pd.DataFrame({"cod6": ["a", "b"], "uf": ["AC", "AC"]})
    polos = pd.DataFrame({"cod6": ["a"], "ano": [2014], "n_polos": [1]})
    internacoes = pd.DataFrame({"cod6": ["a", "b"], "ano": [2013, 2014],
                                "grupo": ["avc", "avc"], "internacoes": [3, 2]})
    pop = pd.DataFrame({"cod6": ["a", "a", "b", "b"], "ano": [2013, 2014] * 2,
                        "populacao": [10.0, 11.0, 5.0, 6.0], "populacao_imputada": [False] * 4})
    p = montar_painel(mun, [2013, 2014], polos, internacoes, pop)
    assert len(p) == 4 and not p.duplicated(["cod6", "ano"]).any()
    assert p["n_polos"].tolist() == [0, 1, 0, 0]
    assert p["int_avc"].tolist() == [3, 0, 0, 2]
    assert {"int_hipertensao", "int_diabetes", "int_apendicite", "int_outras"} <= set(p.columns)


def test_checkpoint(tmp_path):
    chamadas = []

    def gerar():
        chamadas.append(1)
        return pd.DataFrame({"x": [1, 2]})

    arquivo = tmp_path / "parte.parquet"
    assert com_checkpoint(arquivo, gerar)["x"].sum() == 3
    assert com_checkpoint(arquivo, gerar)["x"].sum() == 3
    assert len(chamadas) == 1  # a segunda chamada leu do disco


def test_ler_parquets_coluna_ausente_nao_le_o_resto(tmp_path):
    caminho = tmp_path / "f.parquet"
    pd.DataFrame({"A": ["1"], "SENSIVEL": ["x"]}).to_parquet(caminho)
    df = _ler_parquets([str(caminho)], ["A", "INEXISTENTE"])
    assert list(df.columns) == ["A"]


def test_mde():
    assert abs(mde(1.0) - 2.8016) < 1e-3


def test_baixar_datasus_com_caminho_so_com_nome(tmp_path, monkeypatch):
    """Reproduz o caso do Colab: o PySUS devolve só o nome do arquivo."""
    import pysus

    from appd import download as dl

    cache = tmp_path / "cache"
    pasta = cache / "downloads" / "ftp" / "cnes" / "IN"
    pasta.mkdir(parents=True)
    monkeypatch.setattr(dl, "CACHE_DIR", cache)

    def cnes_falso(**kwargs):
        pd.DataFrame({"CNES": ["1"], "CODUFMUN": ["120040"], "CPF_CNPJ": ["sigiloso"],
                      "INCENTIV": ["8112"]}).to_parquet(pasta / "INAC1512.parquet")
        (pasta / "INAC1512.dbc").write_bytes(b"bruto")
        return ["INAC1512.parquet"]

    monkeypatch.setattr(pysus.ftp, "cnes", cnes_falso)
    df = dl.baixar_datasus("cnes", "AC", 2015, 12, grupo="IN", colunas=["CNES", "INCENTIV"])
    assert list(df.columns) == ["CNES", "INCENTIV"]  # CPF_CNPJ não é lido
    assert not (pasta / "INAC1512.parquet").exists()  # bruto apagado
    assert not (pasta / "INAC1512.dbc").exists()

    cnes_falso()
    esquema = dl.esquema_datasus("cnes", "AC", 2015, 12, grupo="IN")
    assert "INCENTIV" in set(esquema["coluna"])
    assert not (pasta / "INAC1512.parquet").exists()
