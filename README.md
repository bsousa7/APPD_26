# Trabalho Final — APPD (IDP, 2026): Programa Academia da Saúde

**Disciplina:** Avaliação de Políticas Públicas com Dados — Mestrado Profissional em Administração Pública, IDP
**Professor:** Hélio Bomfim de Macêdo Filho
**Integrantes:** [PREENCHER]

## Pergunta

A implantação do primeiro polo do Programa Academia da Saúde reduziu as internações
por doenças hipertensivas, AVC e diabetes nos municípios que o adotaram?
Estimando: ATT. Unidade: município × ano, 2008–2024.
Métodos: escore de propensão e diferenças-em-diferenças (estudo de eventos, TWFE,
Callaway & Sant'Anna). O plano completo está em [`PLANO.md`](PLANO.md).

## Estado atual

| Fase | Situação |
|---|---|
| 0 — Estrutura, ambiente, configuração do Claude Code | Feito (estrutura, `.gitignore`, `requirements.txt`, `CLAUDE.md`, `.claude/settings.json`) |
| 0.5 — Teste de fumaça dos dados | Caderno `notebooks/00_teste_acesso.ipynb` pronto, **a executar localmente** |
| 0.6 — LaTeX | Template copiado e adaptado em `artigo/`; **compilação a testar localmente** |
| 1 — Pergunta, estimando, DAG | DAG, teste de backdoor e `fig01_dag.png` feitos (a revisar); literatura pendente |
| 2 — Esqueleto dos cadernos | Feito (`01_extracao`, `02_analise`) |
| 3 a 9 | Pendentes |

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/01_extracao.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_analise.ipynb
cd artigo && latexmk -xelatex main-artigo.tex
```

**Google Colab:** os cadernos podem ser abertos isolados. A primeira célula de
código clona este repositório na sessão do Colab e passa a trabalhar em
`APPD_26/notebooks/`. No Colab, a instalação usa `requirements-colab.txt`, que
acrescenta só as bibliotecas ausentes (PySUS, linearmodels, differences, sidrapy)
sem trocar as versões do próprio Colab; o caderno imprime as versões efetivas.
O aviso de conflito entre `holidays` e `python-dateutil` pode ser ignorado: o PySUS
fixa `python-dateutil==2.8.2` e o pacote `holidays` não é usado. Os arquivos gerados ficam nessa cópia temporária, que some
quando a sessão termina: baixe o que precisar ou faça commit a partir dela.

Testes das funções auxiliares: `python -m pytest tests -q`.

**Tempo estimado:** [PREENCHER após a primeira execução completa do caderno 01].

## Dependências externas

- Acesso ao FTP do DATASUS (`ftp.datasus.gov.br`), à API de localidades e ao SIDRA do IBGE.
  Se o FTP falhar, `src/appd/download.py` usa o catálogo-espelho do PySUS e registra a troca.
- TeX Live com `latexmk`, `xelatex`, `biber` e a fonte Times New Roman (ou Overleaf).
- Python 3.11 a 3.13 (versões em `requirements.txt`; ferramentas de execução e teste em `requirements-dev.txt`).

## Estrutura

```
notebooks/   00 (teste, não entregue), 01_extracao, 02_analise
src/appd/    download, agregacao, estimacao
data/raw/    vazio na entrega (o caderno 01 baixa os dados)
data/processed/  bases agregadas e dicionários
outputs/     figuras/ e tabelas/ usadas no artigo
artigo/      main-artigo.tex (template LaTeX do IDP adaptado)
docs/ia/     registro de uso de IA e conversas exportadas
```

## Créditos

O diretório `artigo/` deriva do [TemplateLatexIDP](https://github.com/alexlopespereira/TemplateLatexIDP)
(commit `717f75f`), sob a licença em `artigo/LICENSE`. A classe `idp.cls` não foi alterada.

## Uso de IA

Ver `docs/ia/registro-uso-ia.md` e a declaração nos cadernos e no artigo.
