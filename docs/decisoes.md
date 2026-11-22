# Registro de decisões de desenho e de dados

Decisões tomadas pelos autores, com data, motivo e evidência. As decisões de
limpeza com contagem de registros afetados ficam também em markdown nos cadernos.

| Data | Decisão | Motivo / evidência | Onde se aplica |
|---|---|---|---|
| 2026-11-22 | As coortes de tratamento começam em 2014–2015; pré-tratamento 2008–2013. Amostra PSM: coortes 2014–2015 contra nunca tratados. Robustez R7: coortes a partir de 2015 (excluir a coorte 2014) | O tipo de estabelecimento 74 (Polo Academia da Saúde) foi criado pela Portaria SAS/MS nº 24/2014. O teste de fumaça encontrou 0 estabelecimentos tipo 74 no CNES-ST de DF, dez/2012. Polos implantados entre 2011 e 2013 só aparecem quando o tipo passa a existir, de modo que a coorte 2014 pode misturar implantações anteriores | `PLANO.md` (seções 1, 4.4, 4.6, 7 e 10); `notebooks/01_extracao.ipynb` (`ANO_PRIMEIRA_COORTE`); `notebooks/02_analise.ipynb` (seção 1) |
| 2026-11-22 | **Decisão anterior em revisão.** A premissa de que o tipo 74 só existe desde 2014 foi refutada pelo teste de fumaça executado: PE tem 137 estabelecimentos tipo 74 em dez/2012 (175 em 2013, 201 em 2014); o DF tem 0 em todos os anos de 2012 a 2016, o que é específico do DF. O ano da primeira coorte será redefinido pelos autores após a varredura nacional (seção 2b do `00_teste_acesso.ipynb`) | Saída do `notebooks/00_teste_acesso.ipynb`, seção 2, executado pelos autores no Colab em 22/11/2026 | Até a nova decisão, valem as alterações de 22/11/2026 em `PLANO.md`, marcadas como provisórias |
