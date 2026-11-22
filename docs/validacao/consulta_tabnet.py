"""Consulta ao TabNet/DATASUS para conferir a agregação do SIH feita no caderno 01.

Uso (precisa de acesso a tabnet.datasus.gov.br):
    python docs/validacao/consulta_tabnet.py 2015
    python docs/validacao/consulta_tabnet.py 2015 --so-hospitais-do-ac

Formulário: "Morbidade Hospitalar do SUS - por local de residência - Acre"
(sih/cnv/nrac.def), internações por ano de processamento (arquivos nracAAMM),
filtradas pelos itens da Lista de Morbidade CID-10 que correspondem aos
grupos de CID do caderno. Com --so-hospitais-do-ac, filtra os 27
estabelecimentos do Acre, para comparar com o MODO_TESTE do caderno 01 (que só
lê os arquivos RD do AC).
"""

import argparse
import html
import re
import subprocess
import tempfile
import time
import urllib.parse

URL_FORM = "https://tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/nrac.def"
URL_TAB = "https://tabnet.datasus.gov.br/cgi/tabcgi.exe?sih/cnv/nrac.def"

# Itens da "Lista Morb CID-10" do TabNet que formam cada grupo do caderno.
GRUPOS = {
    "hipertensao": ["169", "170"],          # I10; I11–I15
    "avc": ["177", "178", "179", "180"],    # I60–I62; I63; I64; I65–I69
    "diabetes": ["124"],                    # E10–E14
    "apendicite": ["210"],                  # K35–K38
    "total": None,                          # todas as causas
}


def _curl(argumentos, saida):
    for _ in range(8):  # o servidor do TabNet às vezes corta a conexão
        r = subprocess.run(["curl", "-sS", "--http1.1", "-A", "Mozilla/5.0", "-o", saida, *argumentos],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return open(saida, encoding="latin1").read()
        time.sleep(15)
    raise RuntimeError(r.stderr)


def consultar(ano, itens, so_ac, filtros):
    campos = [("Linha", "Município"), ("Coluna", "--Não-Ativa--"), ("Incremento", "Internações")]
    campos += [("Arquivos", f"nrac{ano % 100:02d}{m:02d}.dbf") for m in range(1, 13)]
    for nome, n_opcoes in filtros:
        if nome == "SEstabelecimento" and so_ac:
            campos += [(nome, str(v)) for v in range(1, n_opcoes)]
        elif nome == "SLista_Morb__CID-10" and itens:
            campos += [(nome, v) for v in itens]
        else:
            campos.append((nome, "TODAS_AS_CATEGORIAS__"))
    campos += [("formato", "prn"), ("mostre", "Mostra")]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(urllib.parse.urlencode(campos, encoding="latin1"))
    texto = _curl(["-H", "Content-Type: application/x-www-form-urlencoded",
                   "--data-binary", f"@{f.name}", URL_TAB], f.name + ".html")
    pre = re.search(r"(?is)<PRE>(.*?)</PRE>", texto)
    return html.unescape(pre.group(1)) if pre else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ano", type=int)
    ap.add_argument("--so-hospitais-do-ac", action="store_true")
    ap.add_argument("--municipio", default="120040 RIO BRANCO")
    a = ap.parse_args()
    form = _curl([URL_FORM], tempfile.mktemp(suffix=".html"))
    filtros = []
    for m in re.finditer(r'(?i)<SELECT[^>]*NAME="(S[^"]+)"', form):
        fim = form.lower().find("</select>", m.end())
        filtros.append((m.group(1), len(re.findall(r"(?i)<OPTION", form[m.end():fim]))))
    for grupo, itens in GRUPOS.items():
        r = consultar(a.ano, itens, a.so_hospitais_do_ac, filtros)
        mun = re.search(rf'"{re.escape(a.municipio)}";(\d+)', r)
        tot = re.search(r'"Total";(\d+)', r)
        print(f"{a.ano} {grupo:12s} {a.municipio}: {mun.group(1) if mun else '-':>6} | "
              f"AC: {tot.group(1) if tot else '-':>6}")


if __name__ == "__main__":
    main()
