# Trabalho Final — APPD (IDP, 2026): Programa Academia da Saúde

**Disciplina:** Avaliação de Políticas Públicas com Dados — Mestrado Profissional em Administração Pública, IDP
**Professor:** Hélio Bomfim de Macêdo Filho
**Integrantes:** [PREENCHER]

## Pergunta

A implantação do primeiro polo do Programa Academia da Saúde reduziu as internações
por doenças hipertensivas, AVC e diabetes nos municípios que o adotaram?
Estimando: ATT. Unidade: município × ano, 2008–2024, com coortes de adoção a partir
de 2013 (os municípios com polo já em 2011–2012 saem da amostra principal; ver
[`docs/decisoes.md`](docs/decisoes.md)).
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
| 3 — Extração | **Concluída** (24/11/2026): `01_extracao` executado no Colab em modo completo; painel de 94.707 linhas (5.571 municípios × 17 anos) conferido com o TabNet ([`docs/validacao/`](docs/validacao/)) |
| 4 — Base analítica e descritiva | `02_analise`, seções 3 e 4, implementadas e testadas com dados fictícios; **a executar no Colab** |
| 5 a 9 | Pendentes |

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/01_extracao.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_analise.ipynb
cd artigo && latexmk -xelatex main-artigo.tex
```

**Google Colab:** abra sempre pelos links abaixo, que carregam a versão atual do GitHub
(uma aba já aberta ou uma cópia salva no Drive continua com a versão antiga):

- [00_teste_acesso](https://colab.research.google.com/github/bsousa7/APPD_26/blob/claude/friendly-mayer-jzxwk1/notebooks/00_teste_acesso.ipynb)
- [01_extracao](https://colab.research.google.com/github/bsousa7/APPD_26/blob/claude/friendly-mayer-jzxwk1/notebooks/01_extracao.ipynb)
- [02_analise](https://colab.research.google.com/github/bsousa7/APPD_26/blob/claude/friendly-mayer-jzxwk1/notebooks/02_analise.ipynb)

(Se a branch for renomeada ou mesclada na `main`, troque `claude/friendly-mayer-jzxwk1` por `main` nos links.)
Os cadernos podem ser abertos isolados. A primeira célula de
código clona este repositório na sessão do Colab e passa a trabalhar em
`APPD_26/notebooks/`. No Colab, a instalação usa `requirements-colab.txt`, que
acrescenta só as bibliotecas ausentes (PySUS, linearmodels, differences, sidrapy)
sem trocar as versões do próprio Colab; o caderno imprime as versões efetivas.
O aviso de conflito entre `holidays` e `python-dateutil` pode ser ignorado: o PySUS
fixa `python-dateutil==2.8.2` e o pacote `holidays` não é usado. Os arquivos gerados ficam nessa cópia temporária, que some
quando a sessão termina: baixe o que precisar ou faça commit a partir dela.
Na primeira execução no Colab, a célula de instalação pode parar pedindo para
reiniciar a sessão (troca de versão do numpy). Reinicie em "Ambiente de execução >
Reiniciar sessão" e execute tudo de novo **desde a primeira célula de código**.

**Extração (`01_extracao.ipynb`).** Execute primeiro com `MODO_TESTE = True` (Acre,
2014–2015, poucos minutos) e confira, na seção 6.5, um município-ano com o TabNet. Depois
mude para `MODO_TESTE = False` e execute tudo de novo. Até três partes (UFs) são baixadas ao mesmo tempo (`SIMULTANEOS = 3`), e cada parte (uma UF em um ano) é
gravada assim que termina; se a sessão cair, basta executar de novo, e só as partes que
faltam são baixadas. No Colab, a célula de ambiente pede para montar o Google Drive e os
resultados ficam em `MyDrive/APPD_26_dados/processed`.

Testes das funções auxiliares: `python -m pytest tests -q`.

**Tempo estimado:** extração completa do caderno 01 em cerca de 12 horas no Colab gratuito, com 3 UFs simultâneas, em mais de uma sessão (a primeira execução teve conflitos internos do PySUS, depois corrigidos). Com as partes já gravadas no Drive, uma nova execução leva cerca de 1 minuto. [Revisar após a reexecução integral da Fase 8.]

## Dependências externas

- Acesso ao FTP do DATASUS (`ftp.datasus.gov.br`), à API de localidades e ao SIDRA do IBGE.
  Se o FTP falhar, `src/appd/download.py` usa o catálogo-espelho do PySUS e registra a troca.
- TeX Live com `latexmk`, `xelatex`, `biber` e a fonte Times New Roman (ou Overleaf).
- Python 3.11 a 3.13 (versões em `requirements.txt`; ferramentas de execução e teste em `requirements-dev.txt`).

## Estrutura

```
notebooks/   00 (teste, não entregue), 01_extracao, 02_analise
src/appd/    download, agregacao, armazenamento, analise, estimacao
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
