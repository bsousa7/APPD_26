# Instruções do projeto — Trabalho Final APPD (IDP, 2026)

## Contexto
Avaliação causal do Programa Academia da Saúde sobre internações por doenças
hipertensivas, AVC e diabetes (município × ano, 2008–2024). Métodos: escore de
propensão (Módulo 03) e DiD com Callaway & Sant'Anna (Módulo 04). Plano completo
em PLANO.md. As regras do professor estão nas seções 2 e 3 do PLANO.md e são
obrigatórias.

## Regras invioláveis
1. Todo dado entra pelo código dos cadernos (download das fontes originais).
   Nunca criar, editar ou "corrigir" arquivos de dados à mão.
2. Caminhos sempre relativos à raiz. Identificadores (IBGE, CNES, CID) sempre como texto.
3. Após cada construção de base, incluir `assert` de linhas, chave única e faltantes.
4. `SEMENTE = 42` em toda operação aleatória.
5. Não ler `data/raw/`. Para entender colunas, usar `data/processed/dicionarios/`.
6. Não escrever interpretação de resultados nem conclusões do artigo. Pode
   revisar forma, LaTeX e consistência de números.
7. Não inventar nem completar referências. Só entram no .bib itens que o autor
   verificou na fonte original.
8. Números do artigo vêm de `outputs/tabelas/*.tex` e `outputs/figuras/*.png`;
   nunca redigitar valores.
9. Não editar `artigo/idp.cls`.
10. Cada célula de código precisa de markdown antes (o que e por quê) e depois
    (o que o resultado mostra).

## Bibliotecas (alinhadas aos cadernos da disciplina)
pandas, numpy, statsmodels, scikit-learn (LogisticRegression, GradientBoostingClassifier,
CalibratedClassifierCV, NearestNeighbors), linearmodels (PanelOLS), differences (ATTgt),
pysus, sidrapy, matplotlib, seaborn, networkx, graphviz.

Observação: o PySUS 2.x mudou a API. Use `pysus.ftp.cnes(...)`, `pysus.ftp.sih(...)`
e `pysus.ftp.sim(...)`, com `source="origin"` (FTP do DATASUS). O wrapper fica em
`src/appd/download.py`.

## Comandos
- Testes das funções auxiliares: `python -m pytest tests -q`
- Executar caderno: `jupyter nbconvert --to notebook --execute --inplace notebooks/02_analise.ipynb`
- Compilar artigo: `cd artigo && latexmk -xelatex main-artigo.tex` (ler o .log depois)

## Ao terminar uma tarefa
Resumir o que mudou, o que o autor precisa revisar e lembrar de registrar a
sessão em docs/ia/registro-uso-ia.md.
