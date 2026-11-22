# Plano de Desenvolvimento — Trabalho Final

**Disciplina:** Avaliação de Políticas Públicas com Dados (APPD) — Mestrado Profissional em Administração Pública, IDP
**Professor:** Hélio Bomfim de Macêdo Filho
**Política avaliada:** Programa Academia da Saúde (Ministério da Saúde, Portaria GM/MS nº 719/2011; redefinido pela Portaria GM/MS nº 2.681/2013)
**Entrega:** 31/12/2026
**Execução:** Claude Code + repositório GitHub
**Versão do plano:** 22/11/2026 (revisão 1: coortes a partir de 2014; ver "Registro de alterações" abaixo)

> Este plano foi construído a partir de três documentos, consultados em 21/11/2026:
> - **Orientações para o Trabalho Final**, versão de 14/11/2026 (`trabalho/orientacoes.ipynb`).
> - **Política de Uso de IA na Pós-Graduação Stricto Sensu do IDP**, versão 1.0, 2026 (`trabalho/Politica de Uso de IA.pdf`).
> - **Template LaTeX do IDP** (`alexlopespereira/TemplateLatexIDP`, commit `717f75f`, de 16/11/2026).
>
> Se algum desses documentos mudar, refaça a Fase 0, passo 0.6.

**Registro de alterações**

| Data | Alteração | Motivo |
|---|---|---|
| 22/11/2026 | Pré-tratamento passa a 2008–2013 e as coortes começam em 2014–2015 (antes: pré 2008–2011 e coortes desde 2012). Amostra PSM: coortes 2014–2015. Nova robustez R7 (excluir a coorte 2014) e novo risco na seção 10 | O tipo de estabelecimento 74 só foi criado pela Portaria SAS/MS nº 24/2014; o teste de fumaça encontrou zero polos tipo 74 em DF, dez/2012. Decisão dos autores, registrada em `docs/decisoes.md` |

---

## Sumário

1. [Visão geral do trabalho](#1-visão-geral-do-trabalho)
2. [Matriz de requisitos do professor](#2-matriz-de-requisitos-do-professor)
3. [Política de uso de IA aplicada ao Claude Code](#3-política-de-uso-de-ia-aplicada-ao-claude-code)
4. [Desenho de pesquisa](#4-desenho-de-pesquisa)
5. [Fontes de dados](#5-fontes-de-dados)
6. [Estrutura do repositório](#6-estrutura-do-repositório)
7. [Fases de execução](#7-fases-de-execução)
8. [Artigo em LaTeX: adaptação do template IDP](#8-artigo-em-latex-adaptação-do-template-idp)
9. [CLAUDE.md sugerido para o repositório](#9-claudemd-sugerido-para-o-repositório)
10. [Riscos e mitigação](#10-riscos-e-mitigação)
11. [Checklist final de entrega](#11-checklist-final-de-entrega)
12. [Pendências a confirmar com o professor](#12-pendências-a-confirmar-com-o-professor)
13. [Referências de partida](#13-referências-de-partida)

---

## 1. Visão geral do trabalho

| Item | Definição |
|---|---|
| **Pergunta causal** | A implantação do primeiro polo do Programa Academia da Saúde reduziu as internações por doenças cardiovasculares e metabólicas sensíveis à atividade física (doenças hipertensivas, AVC e diabetes) nos municípios que o adotaram? |
| **Estimando** | ATT: o efeito médio sobre os municípios tratados, isto é, sobre os que implantaram ao menos um polo |
| **Unidade de análise** | Município × ano |
| **Período** | 2008–2024 no painel principal. Pré-tratamento: 2008–2013. Coortes de adoção: a partir de 2014–2015 (o tipo 74 só existe no CNES desde a Portaria SAS/MS nº 24/2014) até 2022, conforme os dados mostrarem |
| **Tratamento (D)** | Ano do primeiro estabelecimento do **tipo 74, "Polo Academia da Saúde"**, no CNES do município |
| **Desfecho principal (Y)** | Internações SUS por doenças hipertensivas, AVC e diabetes (CID-10 I10–I15, I60–I69, E10–E14), por 10 mil habitantes, por município de residência |
| **Desfechos secundários** | Cada grupo de CID em separado; óbitos por doenças hipertensivas (SIM), se a cobertura temporal permitir |
| **Desfecho placebo** | Internações por apendicite (CID-10 K35–K38), que não deveriam responder ao programa |
| **Método 1 (Módulo 03)** | Escore de propensão (logit e gradient boosting calibrado), com pareamento por vizinho mais próximo com caliper e IPW. Inclui balanceamento (SMD) antes e depois, love plot, suporte comum e IC 95% |
| **Método 2 (Módulo 04)** | DiD: estudo de eventos e pré-tendências; TWFE com erros clusterizados por município; placebo; decomposição de Goodman-Bacon; Callaway & Sant'Anna (`differences.ATTgt`) |
| **Robustez** | Tratamento alternativo (polos com incentivo de custeio 81.12/81.13 no CNES); exclusão de municípios pequenos; desfechos separados; janelas alternativas; coortes a partir de 2015 (R7); efeito mínimo detectável (MDE) |
| **Entregas** | `notebooks/01_extracao.ipynb`, `notebooks/02_analise.ipynb` (os dois executados), artigo em PDF (LaTeX, 8–15 páginas) e repositório GitHub público com a estrutura da seção 7 das orientações |

**Por que essa política funciona com as regras do professor**

- O tratamento e os desfechos saem do DATASUS por código (`PySUS`), sem arquivo preparado por fora.
- O tipo 74 está oficialmente definido no CNES (Portaria SAS nº 24/2014).
- A adoção foi escalonada ao longo de vários anos e por milhares de municípios. Até maio/2015, eram 2.849 municípios e 4.240 polos (fonte secundária a verificar), o que exige um estimador robusto, como Callaway & Sant'Anna.
- Há literatura com PSM + DiD para comparar resultados (seção 13).

---

## 2. Matriz de requisitos do professor

Cada requisito das orientações de 14/11/2026 está ligado à fase do plano que o atende. Use esta tabela como **controle de qualidade** antes da entrega.

### 2.1 Conteúdo por módulo

| Módulo | Exigência | Onde é atendida | Fase |
|---|---|---|---|
| 01 | Pergunta causal e estimando explícitos | Cabeçalho do `02_analise` e Introdução do artigo | 1 e 7 |
| 01 | DAG com confundidores (motivam covariáveis), mediadores e colisores (não controlados) | `outputs/figuras/fig01_dag.png`, seção 1 do caderno, seção 3 do artigo | 1 |
| 01 | Discussão de SUTVA | Markdown no caderno e seção 6 do artigo (transbordamento entre municípios vizinhos) | 1 e 7 |
| 03 | Escore estimado | Logit e GradientBoosting + `CalibratedClassifierCV` | 5 |
| 03 | Diagnóstico de suporte comum | Histogramas sobrepostos do escore e regra de trimming | 5 |
| 03 | Ao menos um estimador baseado no escore | Vizinho mais próximo com caliper + IPW (opcional: duplamente robusto) | 5 |
| 03 | Tabela de balanceamento antes e depois | `tab03_balanceamento.csv`, com SMD < 0,1 como critério | 5 |
| 03 | Estimativa com IC | Bootstrap com semente fixa ou EP analítico | 5 |
| 04 | Tendências paralelas examinadas | Estudo de eventos com leads e lags, mais gráfico de médias por coorte | 6 |
| 04 | TWFE com erros clusterizados | `linearmodels.PanelOLS`, `cluster_entity=True` | 6 |
| 04 | Placebo | Placebo de desfecho (apendicite) e placebo de data (tratamento antecipado em 2 anos) | 6 |
| 04 | Estimador robusto à heterogeneidade | `differences.ATTgt` (Callaway & Sant'Anna), com agregações por evento e por coorte | 6 |

### 2.2 Caderno: as 10 etapas obrigatórias, na ordem

| # | Etapa | Caderno / seção | Fase |
|---|---|---|---|
| 1 | Identificação e pergunta (disciplina, integrantes, pergunta, estimando, DAG, métodos) | `01` e `02`, seção 1 | 1 |
| 2 | Preparação do ambiente (`!pip install`, imports, caminhos relativos, `SEMENTE = 42`) | `01` e `02`, seção 2 | 2 |
| 3 | Download dos dados brutos das fontes originais | `01`, seção 3 | 3 |
| 4 | Descompressão e seleção (lista explícita de arquivos mantidos) | `01`, seção 4 | 3 |
| 5 | Dicionário de variáveis e rótulos de valores **antes** da limpeza | `01`, seção 5 | 3 |
| 6 | Construção e validação da base (com `assert`) | `01`, seção 6, e `02`, seção 3 | 3 e 4 |
| 7 | Análise descritiva, sem leitura causal | `02`, seção 4 | 4 |
| 8 | Métodos causais (hipóteses, diagnósticos, estimativas, IC) | `02`, seções 5 e 6 | 5 e 6 |
| 9 | Robustez e poder (MDE) | `02`, seção 7 | 6 |
| 10 | Síntese e exportação (tabelas `.csv`, figuras `.png`, mesmos nomes do artigo) | `02`, seção 8 | 6 |

### 2.3 Boas práticas exigidas

- [ ] Markdown antes de cada bloco (o que e por quê) e depois (o que o resultado mostra).
- [ ] Caminhos relativos à raiz (`Path("..") / "data" / "raw"`), sem nenhum caminho absoluto.
- [ ] Dependências instaladas no caderno **e** `requirements.txt` com versões fixadas.
- [ ] `SEMENTE = 42` usada em bootstrap, pareamento e amostragens.
- [ ] `assert` após cada construção de base: linhas esperadas, chave única, ausência de faltantes.
- [ ] Identificadores como **texto** (`dtype=str`): código IBGE, CNES, CID.
- [ ] Decisões de dados registradas em markdown, com justificativa e contagem de registros afetados.
- [ ] Funções para o que se repete (estimar, registrar na tabela-síntese).
- [ ] Saídas controladas (`head()`, `describe()`), sem dataframes inteiros e sem avisos irrelevantes.
- [ ] Seções numeradas `##`.
- [ ] Caderno **executado** com "Restart & Run All", com todas as saídas visíveis e sem erro.

### 2.4 Artigo

| Seção | Conteúdo exigido |
|---|---|
| Título, autores, filiação | Título informativo (política, desfecho, lugar, período); nomes completos; disciplina e programa |
| Resumo (≤ 250 palavras) e palavras-chave | Pergunta, dados, métodos, resultado com magnitude e IC, conclusão |
| 1. Introdução | Política e mecanismo; literatura (≥ 3 referências); pergunta; estimando; unidade |
| 2. Dados | Fontes com link e data de acesso; período; cobertura; construção de D, Y e X; decisões de limpeza; descritivas |
| 3. Estratégia empírica | Hipóteses de identificação, equações, erros-padrão, diagnósticos planejados |
| 4. Resultados | Tabelas com estimativa, EP e IC 95%; love plot; estudo de eventos |
| 5. Robustez | Especificações e tratamentos alternativos; poder e MDE |
| 6. Discussão e limitações | O que se pode e o que não se pode afirmar; ameaças; medição |
| 7. Conclusão | Resposta direta, com implicações para a política |
| Declaração de uso de IA | Logo antes das referências, conforme o Anexo II da Política |
| Referências | ABNT (o template usa `biblatex-abnt`), incluindo os artigos dos estimadores |
| Apêndice (opcional) | Dicionário de variáveis, tabelas extras, link do repositório |

**Regras de forma:**
- 8 a 15 páginas, sem contar referências e apêndices.
- Fonte 11 ou 12, espaço 1,5, **margens de 2,5 cm**.
- Toda tabela e figura tem número, título, fonte e nota; é citada no texto; e vem de arquivo gerado pelo caderno.
- Resultados não significativos são reportados com a mesma clareza e com discussão de poder.
- Linguagem causal só onde o desenho a sustenta.
- Escrita impessoal ou na 1ª pessoa do plural, sem relatos de bastidores.

### 2.5 Entrega (seção 7 das orientações)

- Repositório **público** no GitHub (ou `.zip`) chamado `TrabalhoFinal_APPD_<sobrenomes>`.
- `data/raw/` vazio na entrega, porque o caderno baixa os dados.
- `README.md` com pergunta, integrantes, como executar, **tempo estimado** e dependências externas.

---

## 3. Política de uso de IA aplicada ao Claude Code

### 3.1 O que a Política exige (resumo)

| Regra | Artigo | Consequência prática neste trabalho |
|---|---|---|
| Autoria e responsabilidade humana | art. 4º, I; art. 11 | Todo integrante deve conseguir explicar **qualquer linha** do caderno e **qualquer frase** do artigo em arguição |
| Usos incentivados | art. 6º | Discutir o desenho; mapear literatura; gerar e depurar código de download, limpeza, gráficos e análise exploratória. Exigem verificação crítica e declaração quando substantivos |
| Usos condicionados | art. 7º | Redação de trechos, revisão com alteração direta do texto, apoio à interpretação, geração de tabelas e figuras. Exigem declaração, reescrita crítica e transparência sobre prompts |
| Usos vedados | art. 8º | Delegar pergunta, desenho, interpretação ou conclusão; usar conteúdo sem revisão e declaração; **fabricar dados, resultados ou referências**; listar a IA como autora; carregar dados pessoais ou não publicados |
| Proteção de dados | art. 4º, VI | Não carregar bases com CPF, NIS, nome ou endereço. Os microdados do DATASUS usados aqui são públicos e anonimizados, mas a regra de prudência continua valendo |
| Declaração de uso | arts. 9º e 10 | No **cabeçalho do caderno** e no **artigo** (seção própria antes das referências, conforme o Anexo II) |
| Guarda de prompts | art. 10, § 2º | Guardar prompts e saídas relevantes, que o professor pode pedir |
| Especificações da disciplina | Orientações, seção 6 | Reexecução integral do caderno pelos autores; interpretação e conclusão dos autores; **referências verificadas uma a uma** |

### 3.2 Procedimentos concretos com o Claude Code

**a) Impedir que o Claude Code leia dados brutos.** Crie `.claude/settings.json` na raiz do repositório:

```json
{
  "permissions": {
    "deny": [
      "Read(./data/raw/**)",
      "Read(./data/processed/**/*.parquet)",
      "Read(./.env)"
    ]
  }
}
```

Para pedir ajuda com dados, entregue ao Claude Code apenas o **dicionário de variáveis** (`data/processed/dicionarios/*.csv`) ou saídas agregadas (`describe()`, contagens), como recomenda a seção 6 das orientações.

**b) Registro de uso de IA, que vira a declaração.** Mantenha `docs/ia/registro-uso-ia.md` com uma linha por sessão relevante:

| Data | Ferramenta / modelo / versão | Etapa | Propósito | O que foi aceito, alterado ou rejeitado | Arquivo da conversa |
|---|---|---|---|---|---|
| 2026-11-22 | Claude Code / Claude Opus 5.5 | Fase 3 – download CNES | Gerar função de download e agregação | Função revisada; filtro de competência reescrito pelo autor | `docs/ia/sessoes/2026-11-22_fase3.md` |

Ao fim de cada sessão relevante, rode `/export` no Claude Code e salve a conversa em `docs/ia/sessoes/AAAA-MM-DD_faseN.md`. Esses arquivos atendem ao art. 10, § 2º.

**c) Revisão crítica obrigatória antes de cada commit.**
1. Ler o diff inteiro (`git diff`).
2. Rodar a célula ou função.
3. Conferir uma amostra do resultado contra o TabNet/DATASUS (por exemplo, internações de um município num ano).
4. Só então fazer o commit. Na mensagem, indique quando houver código gerado com IA, por exemplo `feat(extracao): agrega SIH por municipio [IA: Claude Code, revisado]`.

**d) O que o Claude Code NÃO deve fazer** (registrado no `CLAUDE.md`, seção 9):
- Escrever as conclusões ou a interpretação final do artigo.
- Inventar ou completar referências: toda referência entra no `.bib` só depois de o autor abrir a fonte original.
- Alterar números do artigo à mão: eles vêm de `outputs/`.

**e) Texto da declaração** (Anexo II, adaptado ao uso efetivo; preencher na Fase 8):

> **DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL**
> Durante a preparação deste trabalho, os autores utilizaram o Claude Code (Anthropic), modelo [nome e versão exatos], entre [data inicial] e [data final], para: (i) discutir o desenho de pesquisa; (ii) apoiar a busca e o mapeamento de literatura, com todas as referências verificadas nas fontes originais; (iii) gerar e depurar código Python de download, extração, limpeza, construção da base, estimação e visualização, nas etapas [listar]; e (iv) revisar a formatação LaTeX do artigo [e, se houver, revisão linguística com alteração direta do texto]. Após o uso dessa ferramenta, os autores revisaram e editaram o conteúdo em conformidade com o método científico, reexecutaram integralmente os cadernos e assumem responsabilidade pelo conteúdo do trabalho. Os prompts e as saídas relevantes estão disponíveis em `docs/ia/` no repositório.

---

## 4. Desenho de pesquisa

### 4.1 Mecanismo esperado

```
Polo implantado → oferta de práticas corporais orientadas e educação em saúde
              → mais atividade física regular entre adultos e idosos
              → melhor controle de pressão arterial e glicemia
              → menos internações por doenças hipertensivas, AVC e diabetes
```

O efeito esperado é **defasado**, porque mudanças de comportamento levam tempo para aparecer nas internações. Isso justifica olhar os efeitos dinâmicos (estudo de eventos) e não só a média.

### 4.2 DAG (Módulo 01)

| Papel | Variável | Justificativa | Controlar? |
|---|---|---|---|
| Tratamento (D) | Primeiro polo tipo 74 no município | — | — |
| Desfecho (Y) | Internações cardiovasculares e metabólicas por 10 mil hab. | — | — |
| Confundidor | Porte populacional | Municípios maiores captam mais recursos e têm perfil de internação diferente | Sim |
| Confundidor | PIB per capita (2010) | A capacidade fiscal afeta a adesão e o acesso a serviços | Sim |
| Confundidor | Cobertura de atenção básica e equipes de Saúde da Família / NASF (2010) | Gestão com APS forte adere mais, e a APS reduz internações sensíveis | Sim |
| Confundidor | Estrutura etária (% de 60+ anos) | Envelhecimento eleva o desfecho e pode orientar a priorização | Sim |
| Confundidor | Taxa de internação pré-tratamento (2008–2010) | Seleção por necessidade e risco de regressão à média | Sim (no escore) |
| Confundidor | Leitos SUS por habitante (2010) | A oferta hospitalar afeta a taxa de internação e o perfil da gestão | Sim |
| Confundidor | UF / região | Política estadual, epidemiologia regional | Sim (efeito fixo ou estrato) |
| Mediador | Nível de atividade física da população; controle da pressão arterial | Canal do efeito | **Não** (sobrecontrole) |
| Colisor | Número de atendimentos registrados em atenção básica após a implantação | Afetado pelo polo (encaminhamentos) e pela carga de doença (Y) | **Não** (viés de colisor) |
| Variável só de D | Data de habilitação de recurso de investimento (portarias) | Afeta o momento do tratamento, não Y diretamente | Não necessário |

**Entregável:** `fig01_dag.png`, desenhado com `graphviz` ou `networkx`, mais uma célula que **testa o critério de backdoor** (`nx.is_d_separator`), como no exercício do Módulo 01.

### 4.3 SUTVA

- **Transbordamento:** moradores de um município vizinho podem usar o polo, o que contamina os controles. Mitigação: usar o município de **residência** (`MUNIC_RES`) e, na robustez, excluir controles vizinhos de tratados (contiguidade, se houver tempo).
- **Versões do tratamento:** existem polos de modalidades diferentes (básica, intermediária, ampliada) e polos "similares". Mitigação: tratamento alternativo pelo incentivo de custeio (81.12/81.13) e discussão no artigo.

### 4.4 Método 1: escore de propensão (Módulo 03)

1. **Amostra transversal:** municípios sem polo tipo 74 até 2013. Tratados: primeiro polo tipo 74 em 2014 ou 2015 (primeiras coortes). Controles: nunca adotaram até o fim do painel.
2. **Covariáveis X, medidas em 2010** (pré-tratamento): as da tabela 4.2.
3. **Escore:** `LogisticRegression` e `GradientBoostingClassifier` com `CalibratedClassifierCV`, comparados pela curva de calibração e pela AUC.
4. **Suporte comum:** histogramas sobrepostos; aparar escores fora de [0,05; 0,95] ou fora da sobreposição, registrando quantos municípios saem.
5. **Estimadores:**
   - Vizinho mais próximo 1:1 com caliper de 0,2 DP do logit do escore, com reposição.
   - IPW com pesos ATT (tratados = 1; controles = e/(1−e)).
   - Opcional: duplamente robusto.
6. **Desfecho do PSM:** variação da taxa de internação entre a média 2008–2010 e a média 2016–2018. É um "PSM-DiD" que dialoga com o Método 2.
7. **Diagnóstico:** tabela de balanceamento (média, DP, SMD) antes e depois, e love plot.
8. **Inferência:** bootstrap com 1.000 réplicas (`SEMENTE`) e IC 95% por percentil.

### 4.5 Método 2: diferenças-em-diferenças (Módulo 04)

1. **Painel:** município × ano, 2008–2024. Coorte g = ano do primeiro polo; nunca tratados com g = 0.
2. **Pré-tendências:** gráfico de médias por coorte e estudo de eventos com janela de −4 a +6, omitindo t = −1.
3. **TWFE:** `PanelOLS(Y, D, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)`.
4. **Goodman-Bacon:** decomposição para mostrar o peso das comparações "tardio contra precoce". Se não houver pacote estável, implementar a versão simplificada do curso ou citar a limitação.
5. **Callaway & Sant'Anna:** `ATTgt(data=painel, cohort_column="g", base_period="varying").fit(formula="taxa")`, com controles nunca tratados e, na robustez, os ainda não tratados. Agregar por evento (`"event"`) e por coorte.
6. **Placebos:**
   - de desfecho: internações por apendicite;
   - de data: tratamento atribuído 2 anos antes;
   - de grupo, se houver tempo: entre coortes tardias usando só o período pré.
7. **Ponderação:** desfecho por 10 mil habitantes. Na robustez, ponderar pela população.

### 4.6 Robustez e poder

| Teste | Descrição |
|---|---|
| R1 | Tratamento = polo com incentivo de custeio (códigos 81.12/81.13 no CNES), ou seja, polo "funcionando" |
| R2 | Excluir municípios com menos de 5 mil habitantes, onde as taxas são ruidosas |
| R3 | Desfechos separados: hipertensão, AVC e diabetes |
| R4 | Controles "ainda não tratados" no C&S |
| R5 | Desfecho em log(1 + taxa) |
| R6 | Mortalidade (SIM) como desfecho alternativo, se a série estiver completa |
| R7 | Coortes a partir de 2015 (excluir a coorte 2014, cujo primeiro registro tipo 74 pode refletir polos implantados entre 2011 e 2013 e cadastrados só quando o tipo foi criado) |
| MDE | Efeito mínimo detectável com poder de 80% e α = 5%, a partir da variância residual e do número de clusters |

---

## 5. Fontes de dados

| Base | Uso | Acesso por código | Granularidade | Verificar na Fase 0 |
|---|---|---|---|---|
| **CNES – Estabelecimentos (ST)** | Tratamento: `TP_UNID == "74"` por município e competência | `PySUS` (`cnes`), ou FTP `ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/ST/STUFAAMM.dbc` | Estabelecimento × mês | Existência do campo `TP_UNID`; primeira competência com tipo 74 (esperada a partir de 2014, após a Portaria SAS/MS nº 24/2014; o teste de fumaça confirmou zero em DF, dez/2012) |
| **CNES – Incentivos (IN)** | Tratamento alternativo R1 (81.12/81.13) | `PySUS` (grupo `IN`) ou FTP `.../Dados/IN/` | Estabelecimento × mês | Layout e nome do campo de incentivo |
| **CNES – Equipes (EP) e Leitos (LT)** | Covariáveis de 2010 (equipes de SF/NASF, leitos SUS) | `PySUS` (grupos `EP`, `LT`) | Estabelecimento × mês | Campos de tipo de equipe e de leito |
| **SIH/SUS – AIH Reduzida (RD)** | Desfechos e placebo | `PySUS` (`sih`), ou FTP `.../SIHSUS/200801_/Dados/RDUFAAMM.dbc` | Internação × mês | Campos `MUNIC_RES`, `DIAG_PRINC`, `ANO_CMPT`; disponibilidade de 2024 completo |
| **SIM – Declarações de óbito** | Desfecho alternativo R6 | `PySUS` (`sim`) | Óbito × ano | Último ano **final** (não preliminar) disponível |
| **IBGE – População estimada** | Denominador das taxas | `sidrapy` (SIDRA, tabela de estimativas populacionais, provavelmente a 6579) | Município × ano | Número da tabela e anos com lacuna (anos de Censo) |
| **IBGE – PIB dos municípios** | Covariável | `sidrapy` (tabela do PIB municipal, provavelmente a 5938) | Município × ano | Número da tabela |
| **IBGE – Censo 2010** | % de idosos, % urbano | `sidrapy` | Município | Tabela adequada |
| **Malha / lista de municípios IBGE** | Chave, UF, região | API de localidades do IBGE (`servicodados.ibge.gov.br/api/v1/localidades/municipios`) | Município | Código de 7 dígitos vs. 6 dígitos do DATASUS |

**Atenção às chaves:** o DATASUS usa código de município com **6 dígitos**, sem o dígito verificador; o IBGE usa **7**. Crie `cod6 = cod_ibge7.str[:6]`, faça a junção sempre como texto e coloque `assert` de cardinalidade após cada junção.

**Volume e tempo:** o SIH-RD de 2008–2024 tem cerca de 27 UFs × 12 meses × 17 anos ≈ 5.500 arquivos `.dbc` (vários GB). Estratégia:
- Baixar UF por UF.
- Ler só as colunas necessárias e **agregar na hora** para município × ano × grupo de CID.
- Gravar em `data/processed/` em `.parquet` ou `.csv`.
- Apagar o bruto depois de agregar.

Para o CNES, use **uma competência por ano** (dezembro), o que dá cerca de 27 × 17 arquivos. Estime e registre o tempo de execução no README.

**Se o FTP do DATASUS falhar:** existe um espelho público do FTP (`datasus-ftp-mirror.nyc3.cdn.digitaloceanspaces.com`). Se usá-lo, documente no caderno a URL e a razão.

---

## 6. Estrutura do repositório

Nome sugerido: `TrabalhoFinal_APPD_<sobrenomes>` (público no GitHub).

```
TrabalhoFinal_APPD_<sobrenomes>/
├── README.md                     # pergunta, integrantes, como executar, tempo estimado, dependências externas
├── requirements.txt              # versões fixadas (pip freeze filtrado)
├── CLAUDE.md                     # instruções para o Claude Code (seção 9 deste plano)
├── PLANO.md                      # este plano
├── .gitignore                    # data/raw/, caches, auxiliares LaTeX
├── .claude/
│   └── settings.json             # bloqueio de leitura de data/raw (seção 3.2a)
├── notebooks/
│   ├── 01_extracao.ipynb         # download, descompressão, seleção, dicionários, agregação (executado)
│   └── 02_analise.ipynb          # painel, descritiva, PSM, DiD, robustez, síntese (executado)
├── src/                          # opcional: funções reutilizadas pelos cadernos
│   └── appd/
│       ├── __init__.py
│       ├── download.py
│       ├── agregacao.py
│       └── estimacao.py
├── data/
│   ├── raw/                      # vazio na entrega (com .gitkeep)
│   └── processed/                # bases agregadas geradas pelo caderno 01
│       └── dicionarios/          # dicionários de colunas e rótulos de valores
├── outputs/
│   ├── figuras/                  # fig01_dag.png, fig02_..., usadas no artigo
│   └── tabelas/                  # tab01_....csv e tab01_....tex (mesmos números)
├── docs/
│   └── ia/
│       ├── registro-uso-ia.md    # registro das sessões (seção 3.2b)
│       └── sessoes/              # conversas exportadas do Claude Code
└── artigo/                       # cópia do TemplateLatexIDP adaptada (seção 8)
    ├── main-artigo.tex
    ├── idp.cls                   # NÃO editar
    ├── referencias.bib
    ├── secoes/
    └── Artigo_<sobrenomes>.pdf   # PDF final compilado
```

`.gitignore` mínimo:

```
data/raw/*
!data/raw/.gitkeep
**/__pycache__/
.ipynb_checkpoints/
*.dbc
*.dbf
artigo/*.aux
artigo/*.log
artigo/*.bbl
artigo/*.bcf
artigo/*.blg
artigo/*.out
artigo/*.toc
artigo/*.run.xml
artigo/*.synctex.gz
artigo/*.fdb_latexmk
artigo/*.fls
.env
```

---

## 7. Fases de execução

Cada fase tem **objetivo**, **passos**, **critério de conclusão** e **prompts sugeridos** para o Claude Code. Não passe para a fase seguinte sem cumprir o critério.

### Fase 0 — Preparação do ambiente e validação do acesso aos dados

**Objetivo:** ter repositório, ambiente Python, Claude Code e LaTeX funcionando, e **provar** que os dados podem ser baixados por código.

**Passos (manuais):**

0.1 **Criar o repositório no GitHub**
1. Acesse github.com → **New repository**.
2. Nome: `TrabalhoFinal_APPD_<sobrenomes>`. Visibilidade: **Public** (as orientações pedem repositório público). Marque *Add a README*.
3. No terminal: `git clone https://github.com/<usuario>/TrabalhoFinal_APPD_<sobrenomes>.git` e `cd TrabalhoFinal_APPD_<sobrenomes>`.
4. Se o trabalho for em grupo: *Settings → Collaborators* → adicione os colegas.

0.2 **Criar o ambiente Python** (versão 3.11 ou 3.12):
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install pysus pandas numpy scipy statsmodels linearmodels differences scikit-learn \
            matplotlib seaborn sidrapy requests pyarrow networkx graphviz jupyter nbconvert
```
`graphviz` também precisa do binário do sistema: `sudo apt install graphviz`, `brew install graphviz` ou o instalador para Windows.

0.3 **Criar a estrutura de pastas** da seção 6: `mkdir -p notebooks src/appd data/raw data/processed/dicionarios outputs/figuras outputs/tabelas docs/ia/sessoes artigo .claude`, depois `touch data/raw/.gitkeep`.

0.4 **Configurar o Claude Code:**
1. Na raiz do repositório, rode `claude`.
2. Crie `CLAUDE.md` (seção 9) e `.claude/settings.json` (seção 3.2a).
3. Copie este plano para `PLANO.md`.
4. Faça o commit.

0.5 **Teste de fumaça dos dados** (caderno temporário `notebooks/00_teste_acesso.ipynb`, que não será entregue):
1. Baixar o CNES-ST de **DF, dez/2012** e conferir se aparece `TP_UNID == "74"`.
2. Baixar o SIH-RD de **DF, jan/2024** e conferir `MUNIC_RES`, `DIAG_PRINC`, `ANO_CMPT`.
3. Baixar a população do IBGE via `sidrapy` para um ano.
4. Anotar as versões: `pip show pysus differences linearmodels`.

0.6 **Instalar e testar o LaTeX** (seção 8):
1. Opção local: TeX Live completo (`latexmk`, `xelatex`, `biber`) e a fonte Times New Roman instalada. Opção alternativa: Overleaf.
2. Clonar `https://github.com/alexlopespereira/TemplateLatexIDP` para uma pasta temporária e compilar o `main.tex` original com `latexmk -xelatex main.tex`.

**Critério de conclusão:** os três downloads de teste funcionam; o tipo 74 aparece no CNES; o template compila; tudo está commitado.

**Prompts sugeridos ao Claude Code:**
- "Leia o PLANO.md e o CLAUDE.md. Crie a estrutura de pastas da seção 6, o `.gitignore` e o `requirements.txt` inicial. Não crie nenhum caderno ainda."
- "Crie `notebooks/00_teste_acesso.ipynb` que baixe, com PySUS, o CNES-ST de DF dez/2012 e o SIH-RD de DF jan/2024 e mostre apenas os nomes das colunas e a contagem de `TP_UNID == '74'`. Não imprima registros."

> Se algum teste falhar (FTP bloqueado, PySUS com API diferente), **pare** e resolva antes de seguir: espelho do FTP, outra versão do PySUS ou download direto via `ftplib`. Registre a solução em markdown.

---

### Fase 1 — Pergunta, estimando e DAG (Módulo 01)

**Objetivo:** fixar o desenho antes de tocar nos dados.

**Passos:**
1. Redigir a pergunta, o estimando (ATT), a unidade, o período e as hipóteses, com base na seção 4 deste plano.
2. Desenhar o DAG em código (`networkx` + `graphviz`), testar o backdoor e exportar `outputs/figuras/fig01_dag.png`.
3. Escrever a discussão de SUTVA (seção 4.3).
4. Ler pelo menos 3 artigos da literatura (seção 13), **abrindo as fontes originais**, e registrar no `artigo/referencias.bib` só o que foi lido.
5. **Discutir a escolha com o professor** (atendimento ou fórum), como recomendam as orientações.

**Critério de conclusão:** células 1 do `02_analise` (cabeçalho, pergunta, DAG) prontas; `fig01_dag.png` gerada; literatura mínima lida e no `.bib`.

**Prompt sugerido:** "Com base na seção 4.2 do PLANO.md, escreva a célula que constrói o DAG do Programa Academia da Saúde com networkx, testa o critério de backdoor para o conjunto de confundidores e salva `outputs/figuras/fig01_dag.png`. Explique cada aresta em markdown para que eu revise."

---

### Fase 2 — Esqueleto dos cadernos

**Objetivo:** criar os dois cadernos com todas as seções numeradas e o cabeçalho obrigatório.

**Passos:**
1. Criar `01_extracao.ipynb` com as seções:
   - 1 Identificação
   - 2 Ambiente
   - 3 Download
   - 4 Descompressão e seleção
   - 5 Dicionários
   - 6 Agregação e validação
   - 7 Gravação em `data/processed/`
2. Criar `02_analise.ipynb` com as seções:
   - 1 Identificação, pergunta e DAG
   - 2 Ambiente
   - 3 Painel e validação
   - 4 Descritiva
   - 5 Método 1 – escore de propensão
   - 6 Método 2 – DiD
   - 7 Robustez e poder
   - 8 Síntese e exportação
3. No cabeçalho dos dois: disciplina, integrantes, pergunta, estimando, métodos e **declaração de uso de IA** (versão preliminar, atualizada no fim).
4. Célula de ambiente: `!pip install ...` com versões, imports, `RAIZ = Path("..")`, `SEMENTE = 42`, `np.random.seed(SEMENTE)`, supressão de avisos irrelevantes.

**Critério de conclusão:** os dois cadernos rodam do início ao fim (com seções vazias) e estão commitados.

---

### Fase 3 — Extração (`01_extracao.ipynb`)

**Objetivo:** baixar, selecionar, documentar e agregar todas as fontes, só por código.

**Passos:**
1. **Lista de municípios (IBGE API):** código de 7 dígitos, `cod6`, UF e região. `assert` de 5.570 municípios (confira o número vigente no ano de referência).
2. **CNES-ST:** para cada UF e cada ano de 2008 a 2024, competência de dezembro. Ler `CNES`, `CODUFMUN`, `TP_UNID`. Agregar `n_polos` por município × ano. Derivar `g` = primeiro ano com `n_polos > 0`.
   - Registrar quantos municípios têm o primeiro registro tipo 74 já em 2014. Parte deles pode ter implantado o polo entre 2011 e 2013 e só ter sido cadastrada quando o tipo foi criado (a robustez R7 trata disso).
3. **CNES-IN:** mesmos anos; identificar estabelecimentos com incentivo 81.12/81.13 e derivar `g_custeio` (robustez R1).
4. **CNES-EP e CNES-LT, competência dez/2010:** equipes de Saúde da Família / NASF e leitos SUS por município (covariáveis).
5. **SIH-RD, 2008–2024:** UF por UF, mês por mês. Ler só `MUNIC_RES`, `DIAG_PRINC`, `ANO_CMPT`, `IDADE`, `COD_IDADE`. Classificar o CID em `hipertensao` (I10–I15), `avc` (I60–I69), `diabetes` (E10–E14) e `apendicite` (K35–K38). Agregar contagens por município × ano × grupo. **Apagar o `.dbc` após agregar.**
6. **SIM (opcional, R6):** óbitos por grupo de causa básica, por município de residência × ano.
7. **IBGE via `sidrapy`:** população por município × ano (interpolar os anos sem estimativa e registrar a decisão), PIB municipal 2010, % de idosos em 2010.
8. **Dicionários:** para cada base bruta, exportar `data/processed/dicionarios/<base>_colunas.csv` (nome, tipo, descrição) e os rótulos de valores relevantes (`TP_UNID`, grupos de CID), **antes** de transformar.
9. **Validação:** `assert` de chave única (município × ano), ausência de faltantes inesperados e totais nacionais plausíveis. Confira **um** município-ano contra o TabNet e registre o valor.
10. Gravar `data/processed/painel_bruto.parquet` (ou `.csv`) e `data/processed/covariaveis_2010.csv`.
11. Registrar em markdown, com data de acesso, cada URL ou chamada usada.

**Critério de conclusão:** o caderno 01 roda do início ao fim em ambiente limpo; os arquivos em `data/processed/` existem; o tempo total está medido e anotado no README.

**Prompts sugeridos:**
- "Implemente em `src/appd/download.py` uma função que baixe o CNES-ST de uma UF e competência via PySUS, leia só `CNES`, `CODUFMUN` e `TP_UNID` como texto, e retorne contagem de estabelecimentos tipo 74 por município. Inclua tratamento de erro e registro da URL. Não leia nada em data/raw diretamente para me mostrar."
- "Implemente a agregação do SIH-RD por município de residência × ano × grupo de CID (seção 4 do PLANO.md), processando UF por UF e apagando os `.dbc` após agregar."

> **Revisão crítica:** antes de aceitar o código de agregação, rode-o para uma UF pequena (AC ou RR) e compare o total de internações por hipertensão de um ano com o TabNet do DATASUS.

---

### Fase 4 — Base analítica e descritiva (`02_analise.ipynb`, seções 3 e 4)

**Passos:**
1. Ler `data/processed/`, juntar painel, população e covariáveis, e calcular as taxas por 10 mil habitantes.
2. Definir as amostras e registrar cada exclusão com contagem:
   - **Amostra DiD:** sem polo tipo 74 até 2013; coortes de 2014 em diante; mais os nunca tratados.
   - **Amostra PSM:** coortes 2014–2015 contra nunca tratados.
3. `assert`: painel balanceado (n_mun × n_anos), sem faltantes em Y e D, D monotônico (uma vez tratado, sempre tratado).
4. Descritiva:
   - Tabela de médias de X e Y por grupo (`tab01_descritiva.csv`).
   - Número de municípios por coorte (`fig02_coortes.png`).
   - Evolução de Y por coorte (`fig03_tendencias.png`).
   - Mapa (opcional).
5. Texto em markdown deixando claro que **não há leitura causal** nessa etapa.

---

### Fase 5 — Método 1: escore de propensão (seção 5 do caderno)

**Passos:**
1. Enunciar em markdown as hipóteses de ignorabilidade e suporte comum.
2. Estimar o escore por logit e por GB calibrado; comparar calibração e AUC; escolher e justificar.
3. Suporte comum: `fig04_suporte_comum.png`; aparar e registrar as exclusões.
4. Pareamento por vizinho mais próximo com caliper e IPW com pesos ATT.
5. Balanceamento antes e depois: `tab02_balanceamento.csv` e love plot `fig05_loveplot.png` (critério |SMD| < 0,1).
6. ATT com bootstrap (1.000 réplicas, `SEMENTE`) e IC 95%; registrar na tabela-síntese.

**Critério de conclusão:** balanceamento atingido (ou, se não, documentado e discutido); ATT com IC.

---

### Fase 6 — Método 2: DiD, robustez e síntese (seções 6 a 8 do caderno)

**Passos:**
1. Enunciar tendências paralelas e ausência de antecipação.
2. Estudo de eventos (`fig06_estudo_eventos.png`), com teste conjunto dos leads.
3. TWFE com cluster por município (`tab03_twfe.csv`).
4. Goodman-Bacon (`fig07_bacon.png`) ou explicação da limitação.
5. Callaway & Sant'Anna com agregação por evento (`fig08_cs_evento.png`) e ATT geral (`tab04_cs.csv`).
6. Placebos: apendicite e data antecipada (`tab05_placebos.csv`).
7. Robustez R1 a R6 (`tab06_robustez.csv`).
8. MDE (`tab07_mde.csv`) e interpretação.
9. **Tabela-síntese** com todos os métodos: estimativa, EP, IC 95%, N e nota (`tab08_sintese.csv`).
10. Exportar cada tabela também em `.tex` (`df.to_latex(...)`, mesmo nome-base) para o artigo usar **os mesmos números**.

**Critério de conclusão:** todas as figuras e tabelas do artigo existem em `outputs/`; "Restart & Run All" funciona.

---

### Fase 7 — Redação do artigo (LaTeX)

**Passos:**
1. Montar o `artigo/` conforme a seção 8 deste plano.
2. Escrever as seções na ordem: **Dados** e **Estratégia empírica**, depois **Resultados**, **Robustez**, **Introdução**, **Discussão e limitações**, **Conclusão** e por último o **Resumo**.
3. Incluir figuras com `\includegraphics{../outputs/figuras/figXX_...png}` e tabelas com `\input{../outputs/tabelas/tabXX_....tex}`. Nunca redigite números.
4. Conferir o vocabulário: "efeito" e "impacto" só nos resultados do desenho causal; "associação" na descritiva.
5. Conferir as páginas (8–15, sem referências e apêndices) e a formatação (margens de 2,5 cm, fonte 12, espaço 1,5).
6. **Interpretação e conclusão são do autor ou do grupo.** O Claude Code pode revisar forma, LaTeX e consistência, mas não redige a conclusão.

**Prompts sugeridos:**
- "Revise `artigo/secoes/04-resultados.tex` apenas quanto à consistência com `outputs/tabelas/tab08_sintese.csv`: aponte qualquer número no texto que não corresponda à tabela. Não reescreva parágrafos."
- "Compile o artigo com latexmk e leia o log. Liste erros, avisos de referência indefinida e overfull boxes."

---

### Fase 8 — Integridade, IA e revisão final

**Passos:**
1. **Referências:** abrir cada item do `.bib` na fonte original e conferir autor, ano, título, periódico e DOI. Remover o que não foi lido.
2. **Declaração de uso de IA:** preencher o modelo da seção 3.2e com modelo e versão exatos e as datas reais. Colocar no cabeçalho dos dois cadernos e no artigo, antes das referências.
3. Conferir `docs/ia/registro-uso-ia.md` e as sessões exportadas.
4. **Reexecução integral pelos autores** em ambiente limpo:
   ```bash
   rm -rf data/raw/* data/processed/* outputs/figuras/* outputs/tabelas/*
   jupyter nbconvert --to notebook --execute --inplace notebooks/01_extracao.ipynb
   jupyter nbconvert --to notebook --execute --inplace notebooks/02_analise.ipynb
   ```
   Medir o tempo e atualizar o README.
5. Recompilar o artigo e conferir que os números batem com o caderno.
6. Buscar marcadores de rascunho: `grep -rn "TODO\|XXX\|\[●\]\|PREENCHER" notebooks artigo`.
7. Ensaio de arguição: cada integrante explica uma seção do caderno sem consultar a IA.

---

### Fase 9 — Entrega

1. Atualizar o `README.md`: pergunta, integrantes, como executar (passo a passo), tempo estimado, dependências externas (Graphviz, TeX, acesso ao FTP do DATASUS) e link do artigo.
2. Garantir `data/raw/` vazio (só `.gitkeep`) e o PDF do artigo em `artigo/Artigo_<sobrenomes>.pdf`.
3. Criar uma *release* ou tag no GitHub: `git tag v1.0-entrega && git push --tags`.
4. Enviar o link do repositório público (ou o `.zip`) pelo canal indicado pelo professor até **31/12/2026**.

---

## 8. Artigo em LaTeX: adaptação do template IDP

### 8.1 Diagnóstico do template

O `TemplateLatexIDP` foi feito para **monografias, dissertações e teses**: tem capa, folha de rosto, ficha catalográfica, folha de aprovação, sumário e capítulos em nova página. Ele diverge das regras de forma do artigo:

| Item | Template IDP (`idp.cls`) | Exigência do artigo (orientações, seção 5) | Solução |
|---|---|---|---|
| Margens | esquerda 3, direita 2, superior 3, inferior 2 cm | **2,5 cm** | `\newgeometry{margin=2.5cm}` em `main-artigo.tex`, sem tocar no `idp.cls` |
| Fonte e entrelinha | Times 12; 1,5 | 11 ou 12; 1,5 | Mantém |
| Seções | Seção primária em nova página | Artigo contínuo | Opção de classe `secaocontinua` |
| Pré-textuais | Capa, rosto, ficha, aprovação, dedicatória... | Título, autores, filiação, resumo | Não chamar `\capa`, `\folhaderosto`, `\fichacatalografica`, `\folhadeaprovacao`; criar um bloco de título simples |
| Resumo | 150–500 palavras (NBR 6028) | **Até 250 palavras** | Limitar a 250 |
| Referências | `biblatex-abnt` (NBR 6023) | ABNT ou APA, consistente | Mantém ABNT |
| Declaração de IA | O template traz `termo-autoria-ia.tex` (Anexo I, para bancas) | **Anexo II**, como seção antes das referências | Criar `secoes/declaracao-ia.tex`. O Anexo I não é exigido pela disciplina |
| Extensão | Sem limite | 8–15 páginas sem referências e apêndices | Conferir no PDF final |

O `CLAUDE.md` do template diz para **não alterar `idp.cls`**. A adaptação fica toda no novo `main-artigo.tex`.

### 8.2 Passo a passo da montagem

1. Copiar o template para dentro do repositório, sem histórico Git:
   ```bash
   git clone --depth 1 https://github.com/alexlopespereira/TemplateLatexIDP /tmp/tpl
   rsync -a --exclude .git --exclude "*.pdf" --exclude "*.docx" --exclude orientacoes-idp /tmp/tpl/ artigo/
   ```
   Mantenha o `LICENSE` do template e cite a origem no README.
2. Criar `artigo/main-artigo.tex` (esqueleto abaixo) e a pasta `artigo/secoes/` com um arquivo por seção.
3. Compilar: `cd artigo && latexmk -xelatex main-artigo.tex`. Ler o `main-artigo.log` (erros começam com `!`).
4. Se algum comando da classe exigir a capa ou a folha de rosto para numerar páginas, ajuste o `main-artigo.tex` (por exemplo, `\pagenumbering{arabic}` após o título). Registre a decisão.

**Esqueleto do `main-artigo.tex`** (ponto de partida; o Claude Code deve ajustar até compilar sem erro):

```latex
\input{config/nivel}
\documentclass[\NivelTrabalho,secaocontinua,links]{idp}

\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{amsmath}
\graphicspath{{../outputs/figuras/}}

\addbibresource{referencias.bib}
\input{config/dados}   % título, autor(es) e programa: fonte única dos metadados

\begin{document}
\newgeometry{margin=2.5cm}   % margens exigidas para o artigo (orientações, seção 5)

%% ---- Bloco de título do artigo (substitui capa e folha de rosto) ----
\begin{center}
  {\large\bfseries \TituloTrabalho}\\[6pt]
  Nome Completo 1; Nome Completo 2; Nome Completo 3; Nome Completo 4\\
  Avaliação de Políticas Públicas com Dados --- \NomePrograma, \NomeInstituicao\\
  \LocalTrabalho, \AnoTrabalho
\end{center}

\input{pretextual/resumo}     % até 250 palavras + palavras-chave
\input{pretextual/abstract}   % opcional

\textual
\input{secoes/01-introducao}
\input{secoes/02-dados}
\input{secoes/03-estrategia-empirica}
\input{secoes/04-resultados}
\input{secoes/05-robustez}
\input{secoes/06-discussao-limitacoes}
\input{secoes/07-conclusao}
\input{secoes/declaracao-ia}  % Anexo II da Política de IA, antes das referências

\postextual
\referencias
\input{postextual/apendices}  % opcional: dicionário de variáveis, link do repositório
\end{document}
```

**Tabelas vindas do caderno:**

```latex
\begin{table}[htbp]
  \caption{Efeito do Programa Academia da Saúde: síntese dos estimadores}
  \label{tab:sintese}
  \input{../outputs/tabelas/tab08_sintese.tex}
  \fonte{Elaboração própria a partir de SIH/SUS, CNES e IBGE (caderno 02, seção 8).}
\end{table}
```

Confira na `idp.cls` o nome exato do comando de fonte e nota (`\fonte`, `\nota` ou equivalente). O `CLAUDE.md` e o `TUTORIAL.md` do template mostram os exemplos.

### 8.3 `config/dados.tex` para o artigo

Preencha `\titulo`, `\autor` (ou use o bloco de título para vários autores), `\programa{Mestrado Profissional em Administração Pública}`, `\local{Brasília-DF}`, `\data{2026}` e as palavras-chave. Os campos de banca, ficha e defesa **não se aplicam** e não devem aparecer no PDF.

---

## 9. CLAUDE.md sugerido para o repositório

Copie o bloco abaixo para `CLAUDE.md` na raiz do repositório.

```markdown
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

## Comandos
- Executar caderno: `jupyter nbconvert --to notebook --execute --inplace notebooks/02_analise.ipynb`
- Compilar artigo: `cd artigo && latexmk -xelatex main-artigo.tex` (ler o .log depois)

## Ao terminar uma tarefa
Resumir o que mudou, o que o autor precisa revisar e lembrar de registrar a
sessão em docs/ia/registro-uso-ia.md.
```

---

## 10. Riscos e mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| FTP do DATASUS instável ou bloqueado | Média | Alto | Teste na Fase 0; retentativas no download; espelho público documentado |
| API do PySUS diferente da documentação (mudanças de versão) | Média | Médio | Fixar a versão no `requirements.txt`; alternativa por `ftplib` + `pyreaddbc` |
| Tempo de download e processamento do SIH muito longo | Alta | Médio | Agregar na hora, apagar `.dbc`, separar o `01_extracao`, registrar o tempo |
| Data de cadastro do tipo 74 diferente da data de implantação (o tipo só existe desde 2014) | Alta | Médio | Coortes a partir de 2014–2015; R7 (excluir a coorte 2014); R1 (incentivo de custeio); discutir no artigo |
| Polo cadastrado sem funcionamento real (erro de medida em D) | Média | Médio | Robustez R1 (incentivo de custeio 81.12/81.13); discutir no artigo |
| Pré-tendências violadas | Média | Alto | Reportar com transparência; dar peso ao C&S e ao PSM-DiD; ponderar pelo escore; discutir limites |
| Poucos municípios nunca tratados (adesão ampla) | Média | Médio | Usar os ainda não tratados como controle no C&S; reportar N por coorte |
| Taxas ruidosas em municípios pequenos | Alta | Baixo | R2 (excluir < 5 mil hab.); ponderação populacional |
| Código gerado por IA que o grupo não sabe explicar | Média | **Alto** (art. 8º, II) | Revisão linha a linha; ensaio de arguição na Fase 8 |
| Referência inexistente ou mal atribuída | Baixa | **Muito alto** (art. 8º, VI) | Só entra no `.bib` o que foi aberto na fonte; verificação final item a item |
| Artigo fora de 8–15 páginas | Média | Médio | Conferir na Fase 7; mover tabelas extras para o apêndice |

---

## 11. Checklist final de entrega

Itens das orientações (seção 7), mais os do plano:

- [ ] O caderno baixa os dados das fontes originais, com URL ou chamada de API no código e data de acesso em markdown
- [ ] Arquivos compactados são extraídos por código e só os necessários são mantidos
- [ ] Dicionário de variáveis e rótulos de valores foram exportados
- [ ] Caminhos são relativos; não há caminho do computador de ninguém
- [ ] "Restart & Run All" executa do início ao fim sem erro, e as saídas estão salvas
- [ ] Há `assert` validando a base analítica
- [ ] Ao menos dois métodos da disciplina (PSM e DiD), com hipóteses enunciadas e diagnósticos
- [ ] DAG com confundidores, mediador e colisor, e discussão de SUTVA
- [ ] TWFE clusterizado, estudo de eventos, placebo e Callaway & Sant'Anna
- [ ] Toda tabela e figura do artigo é gerada pelo caderno e tem o mesmo número lá e cá
- [ ] O artigo segue a estrutura da seção 5 e tem entre 8 e 15 páginas; margens de 2,5 cm, fonte 12, espaço 1,5
- [ ] Resumo com até 250 palavras, com magnitude e IC do resultado principal
- [ ] Declaração de uso de IA no caderno e no artigo (Anexo II), com modelo, versão e datas
- [ ] Referências verificadas e formatadas de modo consistente (ABNT), incluindo os artigos dos estimadores
- [ ] Prompts e saídas relevantes guardados em `docs/ia/`
- [ ] Nenhum marcador de rascunho (`[●]`, `TODO`, `XXX`, `PREENCHER`) no caderno ou no artigo
- [ ] README explica como rodar e quanto tempo leva
- [ ] `data/raw/` vazio no repositório; repositório público; tag `v1.0-entrega`

---

## 12. Pendências a confirmar com o professor

1. **Política escolhida:** confirmar que o Programa Academia da Saúde (com tratamento derivado do CNES) é aceito para o trabalho final.
2. **Template:** confirmar que o artigo pode usar o template LaTeX do IDP com margens ajustadas para 2,5 cm e sem os elementos pré-textuais de dissertação.
3. **Grupo:** confirmar a composição e o número de integrantes, e se é permitido entregar individualmente.
4. **Tamanho do caderno 01:** confirmar se é aceitável que o `01_extracao.ipynb` leve várias horas para executar (download do SIH 2008–2024), com o tempo documentado no README.

---

## 13. Referências de partida

*Todas devem ser abertas e verificadas na fonte original antes de entrar no `.bib`.*

**Política e normas**
- BRASIL. Ministério da Saúde. Portaria GM/MS nº 719, de 7 de abril de 2011. Institui o Programa Academia da Saúde no âmbito do SUS.
- BRASIL. Ministério da Saúde. Portaria GM/MS nº 2.681, de 7 de novembro de 2013. Redefine o Programa Academia da Saúde no âmbito do SUS.
- BRASIL. Ministério da Saúde. Portaria GM/MS nº 2.684, de 8 de novembro de 2013 (incentivos de investimento e custeio).
- BRASIL. Ministério da Saúde. Portaria SAS/MS nº 24, de 14 de janeiro de 2014 (tipo de estabelecimento 74 no SCNES).

**Avaliações do programa (literatura para comparação)**
- Cadernos de Saúde Pública, v. 39, n. 1, 2023, e00012922. DiD ponderado por PSM; internações por AVC. https://scielosp.org/article/csp/2023.v39n1/e00012922
- Ciência & Saúde Coletiva, v. 26, n. 12, p. 6199–6210, 2021. PSM; mortalidade por hipertensão em Pernambuco. https://www.scielo.br/j/csc/a/QPGyrdgRT75LRRPNKmBCBWP/
- Barros, J. R. S. (2024). Impacto do Programa Academia da Saúde sobre os gastos com internações por doenças isquêmicas do coração no Brasil. Dissertação, UFPE.

**Métodos**
- Rosenbaum, P.; Rubin, D. (1983). The central role of the propensity score in observational studies for causal effects. *Biometrika*.
- Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *Journal of Econometrics*.
- Callaway, B.; Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. *Journal of Econometrics*.
- Bertrand, M.; Duflo, E.; Mullainathan, S. (2004). How much should we trust differences-in-differences estimates? *Quarterly Journal of Economics*.
- Cunningham, S. (2021). *Causal Inference: The Mixtape*. Yale University Press.
- Gertler, P. et al. (2018). *Avaliação de Impacto na Prática*. 2. ed. Banco Mundial.

**Dados e ferramentas**
- PySUS: https://pysus.readthedocs.io
- DATASUS, Transferência de arquivos: https://datasus.saude.gov.br/transferencia-de-arquivos/
- IBGE SIDRA: https://sidra.ibge.gov.br
- Template LaTeX IDP: https://github.com/alexlopespereira/TemplateLatexIDP
- Repositório da disciplina: https://github.com/heliomacedofilho/idp_avaliacao_2026
