# Relatório de Mercado Tech Brasil — 2026

**Data de geração:** 29/07/2026 (atualizado em 31/08/2026)
**Fonte:** Glassdoor Brasil, coleta distribuída multi-máquina (versao3)
**Comparativo:** Pipeline Paulo — Glassdoor Brasil 2025

---

## 1. Pipeline de Dados

### 1.1 Bronze — Coleta

O scraper rodou em modo distribuído, com múltiplas máquinas buscando simultaneamente no Glassdoor Brasil. Cada máquina varreu combinações de **palavra-chave × UF**, gerando um arquivo CSV por combinação.

- **9.124 arquivos CSV** coletados na camada bronze
- **~805.000 registros brutos** (com duplicatas entre UFs, máquinas e datas de coleta)
- Colunas brutas: Função, Localização, Empresa, Data de Publicação, URL

### 1.2 Silver — Deduplicação e Enriquecimento

**`deduplicar.py`** consolidou todos os CSVs bronze, removendo duplicatas por URL e por hash de campos.

**`enriquecer.py`** acessou a página de cada vaga e extraiu campos estruturados.

| Etapa | Registros |
|---|---|
| Bronze (bruto) | ~805.000 |
| Silver — vagas únicas | 123.737 |
| Silver — com descrição enriquecida (>50 chars) | 123.161 (99,5%) |
| Silver — com salário informado | 32.758 (26,5%) |

Arquivo consolidado final: `data/silver/vagas_enriquecidas.csv`.

### 1.3 Analytics — Filtragem e Classificação

**`scp_01.ipynb`** — Filtragem para vagas tech
→ **15.869 vagas tech** (de 123.477 únicas após dedup interno)

**`scp_02.ipynb`** — Classificação e limpeza
Classifica Área, Tipo, Nível e Local. Remove blacklist e vagas internacionais.
→ **15.514 vagas** (15.521 após blacklist, −7 internacionais)

**`scp_03.ipynb`** — Extração de skills
Busca 134 skills com word boundaries + sinônimos. Detecta flag IA.
→ **matriz 15.514 × 141 colunas**

**`scp_04.ipynb`** — Análises avançadas
Rankings por classe de skill, domínios, LLMs citadas, NLP de títulos, investigação da queda de ML.

**`scp_analise_softskills.ipynb`** — Amostras e análise de soft skills
Amostragem estratificada por área para validação manual.

**`scp_comparativo.ipynb`** — Comparativo 2025 × 2026
Carga paralela dos dois pipelines com as mesmas 134 skills comparáveis.

---

## 2. Panorama 2026

### 2.1 Volume de Vagas

**15.514 vagas tech** classificadas após filtragem, com **13.135 títulos de cargo únicos**.

### 2.2 Distribuição por Área

| Área | Vagas | % |
|---|---|---|
| Desenvolvimento de Software | 4.758 | 30,7% |
| Projetos e Gerenciamento | 3.349 | 21,6% |
| Infraestrutura e Suporte | 3.188 | 20,5% |
| Dados e Inteligência Artificial | 2.454 | 15,8% |
| Testes e Controle de Qualidade | 1.109 | 7,1% |
| Segurança da Informação | 376 | 2,4% |
| Automação de Processos e Sistemas | 280 | 1,8% |

### 2.3 Nível de Senioridade

| Nível | Vagas | % |
|---|---|---|
| Pleno / Sênior | 7.357 | 47,4% |
| Júnior | 3.431 | 22,1% |
| n/f (não encontrado) | 3.153 | 20,3% |
| Liderança | 1.573 | 10,1% |

**Breakdown das 3.431 vagas Júnior:**

| Subcategoria | Vagas | % |
|---|---|---|
| Auxiliar | 1.762 | 48,5% |
| Júnior | 975 | 26,8% |
| Estágio | 805 | 22,2% |
| Aprendiz | 57 | 1,6% |
| Trainee | 36 | 1,0% |

> Nota: a maioria das vagas classificadas como "Júnior" corresponde, na prática, a vagas de nível auxiliar — cargos de entrada sem progressão técnica clara.

### 2.4 Localização Geográfica

**Top 10 estados:**

| Estado | Vagas | % |
|---|---|---|
| São Paulo | 6.164 | 39,7% |
| Minas Gerais | 1.491 | 9,6% |
| Rio de Janeiro | 1.055 | 6,8% |
| Paraná | 1.048 | 6,8% |
| Santa Catarina | 966 | 6,2% |
| Rio Grande do Sul | 832 | 5,4% |
| Goiás | 503 | 3,2% |
| Pernambuco | 405 | 2,6% |
| Ceará | 398 | 2,6% |
| Distrito Federal | 322 | 2,1% |

**Modalidade de trabalho** (sobre vagas com tipo classificado, n=15.474):

| Modalidade | Vagas | % |
|---|---|---|
| Presencial / Nacional | 14.006 | 90,5% |
| Híbrido | 940 | 6,1% |
| Remoto | 528 | 3,4% |

**Híbrido e remoto por área:**

| Área | Híbrido | Remoto |
|---|---|---|
| Dados e Inteligência Artificial | 10,1% | 3,4% |
| Segurança da Informação | 8,5% | 2,7% |
| Desenvolvimento de Software | 5,9% | 5,5% |
| Projetos e Gerenciamento | 5,8% | 2,5% |
| Infraestrutura e Suporte | 4,8% | 2,1% |
| Testes e Controle de Qualidade | 2,7% | 1,2% |
| Automação de Processos e Sistemas | 1,8% | 2,5% |

### 2.5 Hard Skills

**Top 10 por frequência:**

| Rank | Skill | Vagas | % |
|---|---|---|---|
| 1 | Cloud | 2.877 | 18,5% |
| 2 | SQL | 2.825 | 18,2% |
| 3 | Metodologias Ágeis | 2.704 | 17,4% |
| 4 | Python | 2.393 | 15,4% |
| 5 | API | 2.256 | 14,5% |
| 6 | AWS | 2.137 | 13,8% |
| 7 | Excel | 2.033 | 13,1% |
| 8 | CI/CD | 1.812 | 11,7% |
| 9 | Git | 1.645 | 10,6% |
| 10 | Azure | 1.628 | 10,5% |

**Rankings por classe:**

*Sistemas (plataformas e ambientes):*

| Rank | Sistema | % |
|---|---|---|
| 1 | AWS | 13,8% |
| 2 | Azure | 10,5% |
| 3 | SAP | 7,0% |
| 4 | Kubernetes | 6,6% |
| 5 | Windows | 6,5% |
| 6 | Linux | 6,2% |
| 7 | GCP | 6,0% |
| 8 | React | 5,6% |
| 9 | PostgreSQL | 5,2% |
| 10 | Kafka | 4,8% |

*Ferramentas:*

| Rank | Ferramenta | % |
|---|---|---|
| 1 | Excel | 13,1% |
| 2 | Git | 10,6% |
| 3 | Office 365 | 9,2% |
| 4 | Power BI | 8,1% |
| 5 | Docker | 7,5% |
| 6 | Grafana | 6,0% |
| 7 | Gestão de tarefas | 3,8% |
| 8 | Terraform | 3,6% |
| 9 | Tableau | 2,0% |
| 10 | LangChain | 1,7% |

*Linguagens de programação:*

| Rank | Linguagem | % |
|---|---|---|
| 1 | SQL | 18,2% |
| 2 | Python | 15,4% |
| 3 | JavaScript | 8,9% |
| 4 | Java | 7,9% |
| 5 | Go | 6,1% |
| 6 | TypeScript | 4,1% |
| 7 | C# | 4,0% |
| 8 | HTML | 4,0% |
| 9 | CSS | 3,8% |
| 10 | C++ | 3,0% |

*Conceitos técnicos:*

| Rank | Conceito | % |
|---|---|---|
| 1 | Cloud | 18,5% |
| 2 | Metodologias Ágeis | 17,4% |
| 3 | API | 14,5% |
| 4 | CI/CD | 11,7% |
| 5 | Scrum | 7,7% |
| 6 | Microservices | 5,6% |
| 7 | NoSQL | 5,5% |
| 8 | Kanban | 5,2% |
| 9 | Machine Learning | 5,2% |
| 10 | Data Privacy | 3,5% |

**Domínios mais demandados** (agrupamento por tema, não por skill isolada):

| Rank | Domínio | Vagas |
|---|---|---|
| 1 | Cloud Computing | 3.918 |
| 2 | Banco de Dados | 3.756 |
| 3 | DevOps e Versionamento | 3.214 |
| 4 | Agilidade e Processos | 3.213 |
| 5 | Backend | 2.860 |
| 6 | Dados e BI | 2.645 |
| 7 | Dados | 2.393 |
| 8 | Integração / APIs | 2.288 |
| 9 | Frontend | 1.990 |
| 10 | Sistemas Operacionais | 1.521 |

### 2.6 Soft Skills

**Ranking geral:**

| Rank | Skill | Vagas | % |
|---|---|---|---|
| 1 | Comunicação | 6.460 | 41,6% |
| 2 | Organização | 5.343 | 34,4% |
| 3 | Criatividade / Inovação | 4.671 | 30,1% |
| 4 | Liderança | 2.634 | 17,0% |
| 5 | Trabalho em equipe | 2.465 | 15,9% |
| 6 | Resolução de problemas | 2.249 | 14,5% |
| 7 | Autonomia | 1.603 | 10,3% |
| 8 | Proatividade | 1.539 | 9,9% |
| 9 | Pensamento analítico | 1.371 | 8,8% |
| 10 | Adaptabilidade | 860 | 5,5% |
| 11 | Resiliência | 714 | 4,6% |
| 12 | Gestão do tempo | 714 | 4,6% |
| 13 | Negociação | 605 | 3,9% |
| 14 | Empatia | 465 | 3,0% |
| 15 | Foco em resultados | 465 | 3,0% |
| 16 | Pensamento Crítico | 155 | 1,0% |
| 17 | Gestão de conflitos | 93 | 0,6% |
| 18 | Inteligência Emocional | 78 | 0,5% |

**Soft skills por nível de senioridade (top 5–7 por nível):**

| Soft Skill | Liderança | Júnior | Pleno / Sênior |
|---|---|---|---|
| Comunicação | 52,1% (1º) | 36,9% (2º) | 40,9% (1º) |
| Liderança | 51,6% (2º) | — | 14,2% (6º) |
| Organização | 39,7% (3º) | 40,3% (1º) | 32,5% (3º) |
| Criatividade | 30,5% (4º) | 28,4% (3º) | 33,5% (2º) |
| Trabalho em equipe | 14,9% (5º) | 15,3% (4º) | 18,3% (4º) |
| Resolução de problemas | 14,9% (5º) | 12,8% (6º) | 15,4% (5º) |
| Proatividade | — | 13,2% (5º) | — |
| Negociação | 10,3% (7º) | — | — |
| Autonomia | 10,9% (6º) | — | 13,9% (7º) |

### 2.7 Idiomas

| Idioma | Vagas | % |
|---|---|---|
| Inglês | 2.901 | 18,7% |
| Espanhol | 557 | 3,6% |
| Francês | 64 | 0,4% |
| Alemão | 62 | 0,4% |
| Italiano | 14 | 0,1% |
| Mandarim | 9 | 0,1% |
| Chinês | 0 | — |
| Japonês | 0 | — |

### 2.8 Formação

| Formação | Vagas | % |
|---|---|---|
| Engenharia (qualquer) | 4.785 | 30,8% |
| Técnico | 4.176 | 26,9% |
| Graduação (qualquer) | 2.362 | 15,2% |
| Administração | 2.273 | 14,7% |
| Ciência da Computação | 1.573 | 10,1% |
| Sistemas de Informação | 1.427 | 9,2% |
| Pós-Graduação | 1.098 | 7,1% |
| Engenharia de Software | 807 | 5,2% |
| Engenharia da Computação | 617 | 4,0% |

**Pós-graduação por nível de senioridade:**

| Nível | % que pede pós | Vagas |
|---|---|---|
| Liderança | 10,6% | 166 |
| Pleno / Sênior | 4,8% | 351 |
| n/f | 4,5% | 143 |
| Júnior | 1,9% | 64 |

### 2.9 Salários

**2.043 vagas com salário informado (12,9%)**
*(Nota: dado subestimado — ver Seção 4)*

| Faixa salarial (R$ mil/mês) | Vagas | % |
|---|---|---|
| Abaixo de R$ 2k | 636 | 31,1% |
| R$ 2k – R$ 5k | 994 | 48,7% |
| R$ 5k – R$ 10k | 295 | 14,4% |
| R$ 10k – R$ 30k | 117 | 5,7% |
| Acima de R$ 30k | 1 | 0,1% |

### 2.10 Inteligência Artificial

**3.837 vagas com foco em IA (24,7% do total)**

| Área | % vagas com IA |
|---|---|
| Dados e Inteligência Artificial | 50,8% |
| Projetos e Gerenciamento | 23,1% |
| Desenvolvimento de Software | 22,4% |
| Automação de Processos e Sistemas | 18,9% |
| Segurança da Informação | 18,9% |
| Infraestrutura e Suporte | 15,2% |
| Testes e Controle de Qualidade | 12,9% |

**LLMs citadas explicitamente nas descrições de vagas:**

| LLM | Vagas | % do total |
|---|---|---|
| Claude | 392 | 2,5% |
| Cursor | 163 | 1,1% |
| ChatGPT | 155 | 1,0% |
| Gemini | 154 | 1,0% |
| Grok | 6 | 0,0% |
| Deepseek | 2 | 0,0% |
| Kimi | 2 | 0,0% |
| **Qualquer LLM** | **528** | **3,4%** |

> Claude lidera por menção direta, concentrado em Dados/IA (5,1%) e Desenvolvimento de Software (3,2%). Cursor é o mais citado em vagas de liderança (1,7%). ChatGPT e Gemini são distribuídos de forma mais homogênea entre áreas e níveis.
>
> Co-ocorrências: 73,6% das vagas com Cursor também mencionam Claude; 67,1% das vagas com ChatGPT também mencionam Claude — sugerindo que Claude funciona como benchmark de referência nas descrições.

**LLMs por nível de senioridade:**

| LLM | Liderança | Júnior | Pleno / Sênior | n/f |
|---|---|---|---|---|
| Claude | 3,1% | 1,0% | 3,3% | 2,2% |
| ChatGPT | 1,1% | 1,0% | 1,2% | 0,4% |
| Cursor | 1,7% | 0,3% | 1,1% | 1,5% |
| Gemini | 0,6% | 0,7% | 1,4% | 0,4% |

---

## 3. Comparativo 2025 vs 2026

**Base de comparação:** Pipeline Paulo 2025 (Glassdoor Brasil) vs Pipeline versao3 2026 (Glassdoor Brasil)
**134 skills comparáveis** entre os dois pipelines.

### 3.1 Volume

| | 2025 | 2026 | Δ |
|---|---|---|---|
| Vagas tech classificadas | 19.293 | 15.514 | −3.779 (−19,6%) |

### 3.2 Distribuição por Área

| Área | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Desenvolvimento de Software | 36,3% | 30,7% | −5,6 |
| Infraestrutura e Suporte | 22,1% | 20,5% | −1,6 |
| Dados e Inteligência Artificial | 17,1% | 15,8% | −1,3 |
| **Projetos e Gerenciamento** | **14,0%** | **21,6%** | **+7,6** |
| Testes e Controle de Qualidade | 5,3% | 7,1% | +1,8 |
| Automação de Processos | 2,8% | 1,8% | −1,0 |
| Segurança da Informação | 2,5% | 2,4% | −0,1 |

> Destaque: Projetos e Gerenciamento cresceu 7,6 pp — a maior variação positiva — enquanto Desenvolvimento caiu 5,6 pp.

### 3.3 Nível de Senioridade

| Nível | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Pleno / Sênior | 50,1% | 47,4% | −2,7 |
| Júnior | 27,0% | 22,1% | −4,9 |
| Liderança | 8,0% | 10,1% | +2,1 |
| n/f | 14,9% | 20,3% | +5,4 |

> Tendência de seniorização: Júnior caiu 4,9 pp, Liderança cresceu 2,1 pp.

### 3.4 Geografia

| Estado | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| **São Paulo** | 26,6% | 39,7% | **+13,1** |
| Minas Gerais | 7,9% | 9,6% | +1,7 |
| Rio de Janeiro | 5,2% | 6,8% | +1,6 |
| Paraná | 6,8% | 6,8% | 0,0 |
| Santa Catarina | 5,3% | 6,2% | +0,9 |
| Rio Grande do Sul | 6,3% | 5,4% | −0,9 |
| Trabalho remoto *(2025)* | 6,5% | — | — |
| n/e *(sem estado, 2025)* | 17,8% | — | — |

> São Paulo concentrou +13,1 pp. Em 2025 havia 17,8% de vagas sem estado (n/e) e 6,5% como "Trabalho remoto" — categorias que em 2026 passaram a ser classificadas por estado + modalidade de trabalho separadamente. A concentração de SP reflete tanto crescimento real quanto melhor cobertura da planilha de cidades em 2026.

### 3.5 Modalidade de Trabalho

| Modalidade | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Nacional / Presencial | 92,1% | 90,5% | −1,6 |
| Híbrido | — | 6,1% | +6,1 |
| Remoto | 7,9% | 3,4% | −4,5 |

> O trabalho flexível (remoto + híbrido) foi de **7,9% em 2025 para 9,5% em 2026** — um crescimento real de +1,6 pp. O que parecia uma queda abrupta no relatório anterior era um artefato: a categoria "remoto" de 2025 englobava vagas hoje corretamente separadas entre remoto e híbrido. O pipeline de 2026 detecta a modalidade pelo texto da descrição da vaga quando a string de localização não indica explicitamente. Dados/IA tem o maior índice de híbrido (10,1%); Dev de Software tem o maior índice de remoto (5,5%).

### 3.6 Hard Skills

| Skill | 2025 (%) | 2026 (%) | Δ pp | Tendência |
|---|---|---|---|---|
| SQL | 21,2% | 18,2% | −3,0 | ↓ |
| Cloud | 19,4% | 18,5% | −0,9 | ↓ |
| Metodologias Ágeis | 20,0% | 17,4% | −2,6 | ↓ |
| Python | 18,3% | 15,4% | −2,9 | ↓ |
| API | 14,8% | 14,5% | −0,3 | ↓ |
| AWS | 14,9% | 13,8% | −1,1 | ↓ |
| CI/CD | 13,0% | 11,7% | −1,3 | ↓ |
| Git | 13,0% | 10,6% | −2,4 | ↓ |
| **Excel** | **9,8%** | **13,1%** | **+3,3** | ↑ |
| JavaScript | 13,2% | 8,9% | −4,3 | ↓ |
| Azure | 11,5% | 10,5% | −1,0 | ↓ |
| R *(¹)* | 22,0% | 0,0% | — | — |
| Scrum | 11,9% | 7,7% | −4,2 | ↓ |
| Office 365 | 9,4% | 9,2% | −0,2 | ↓ |
| Java | 9,1% | 7,9% | −1,2 | ↓ |
| Power BI | 7,8% | 8,1% | +0,3 | ↑ |
| Windows | 9,0% | 6,5% | −2,5 | ↓ |
| Docker | 7,9% | 7,5% | −0,4 | ↓ |
| Linux | 9,2% | 6,2% | −3,0 | ↓ |
| React | 7,9% | 5,6% | −2,3 | ↓ |

> *(¹) R language: o valor de 22% em 2025 é artefato do pipeline daquele ano (padrão `\b(r)\b` capturava a letra "r" isolada). O valor real de 2025 deve ser próximo de zero.*

> **Destaques:** Excel é a única skill entre as top-20 com crescimento relevante (+3,3 pp). O declínio generalizado das demais sugere portfólio mais diversificado — nenhuma skill isolada domina.

### 3.7 Soft Skills

| Skill | 2025 (%) | 2026 (%) | Δ pp | Tendência |
|---|---|---|---|---|
| Comunicação | 36,9% | 41,6% | **+4,7** | ↑ |
| **Organização** | 26,7% | 34,4% | **+7,7** | ↑ |
| Criatividade / Inovação | 31,3% | 30,1% | −1,2 | ↓ |
| **Liderança** | 13,5% | 17,0% | **+3,5** | ↑ |
| Trabalho em equipe | 20,1% | 15,9% | −4,2 | ↓ |
| Resolução de problemas | 14,1% | 14,5% | +0,4 | ↑ |
| Proatividade | 10,3% | 9,9% | −0,4 | ↓ |
| Pensamento analítico | 10,2% | 8,8% | −1,4 | ↓ |
| **Autonomia** | 7,8% | 10,3% | **+2,5** | ↑ |
| Adaptabilidade | 6,8% | 5,5% | −1,3 | ↓ |
| Resiliência | 3,5% | 4,6% | +1,1 | ↑ |
| Gestão do tempo | 3,2% | 4,6% | +1,4 | ↑ |
| Empatia | 3,9% | 3,0% | −0,9 | ↓ |
| Negociação | 2,7% | 3,9% | +1,2 | ↑ |
| Foco em resultados | 2,1% | 3,0% | +0,9 | ↑ |
| Pensamento Crítico | 1,3% | 1,0% | −0,3 | ↓ |
| Gestão de conflitos | 0,5% | 0,6% | +0,1 | ↑ |
| Inteligência Emocional | 0,4% | 0,5% | +0,1 | ↑ |

> Tendência clara: soft skills de **autogestão** cresceram (Organização +7,7 pp, Autonomia +2,5 pp, Liderança +3,5 pp), enquanto **colaboração passiva** caiu (Trabalho em equipe −4,2 pp). Skills de gestão interpessoal (Negociação, Gestão do tempo, Resiliência) também crescem levemente.

### 3.8 Idiomas

| Idioma | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Inglês | 19,0% | 18,7% | −0,3 |
| Espanhol | 3,2% | 3,6% | +0,4 |
| Francês | 0,4% | 0,4% | 0,0 |
| Alemão | 0,4% | 0,4% | 0,0 |

> Idiomas estáveis. Demanda de inglês praticamente não se alterou.

### 3.9 Skills por Área

#### Desenvolvimento de Software

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Comunicação | 33,7% | 38,2% | +4,5 |
| Criatividade | 31,4% | 30,3% | −1,1 |
| API | 28,6% | 29,9% | +1,3 |
| **Organização** | 24,1% | 31,1% | **+7,0** |
| Engenharia | 26,6% | 27,7% | +1,1 |
| JavaScript | 28,1% | 21,5% | −6,6 |
| Git | 25,2% | 22,9% | −2,3 |
| Metodologias Ágeis | 25,4% | 21,4% | −4,0 |
| Técnico | 21,2% | 22,2% | +1,0 |
| SQL | 22,5% | 20,4% | −2,1 |

#### Dados e Inteligência Artificial

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Python | 50,7% | 47,4% | −3,3 |
| SQL | 50,1% | 47,4% | −2,7 |
| Comunicação | 39,5% | 44,8% | +5,3 |
| **Engenharia** | 37,5% | 46,5% | **+9,0** |
| Criatividade | 37,5% | 33,9% | −3,6 |
| **Organização** | 27,7% | 35,2% | **+7,5** |
| Power BI | 31,0% | 30,8% | −0,2 |
| Pensamento analítico | 30,8% | 26,7% | −4,1 |
| Cloud | 23,6% | 26,7% | +3,1 |
| Machine Learning | 28,3% | 21,2% | −7,1 |

#### Infraestrutura e Suporte

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Técnico | 47,0% | 45,1% | −1,9 |
| Comunicação | 37,0% | 43,0% | +6,0 |
| **Organização** | 25,8% | 37,0% | **+11,2** |
| Windows | 28,8% | 22,5% | −6,3 |
| Criatividade | 25,3% | 23,7% | −1,6 |
| Cloud | 22,1% | 22,1% | 0,0 |
| Engenharia | 19,4% | 20,4% | +1,0 |
| Resolução de problemas | 20,4% | 19,2% | −1,2 |
| Administração | 19,1% | 19,5% | +0,4 |
| Linux | 22,3% | 16,0% | −6,3 |

#### Projetos e Gerenciamento

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Comunicação | 43,3% | 45,6% | +2,3 |
| Organização | 34,6% | 36,2% | +1,6 |
| Criatividade | 33,3% | 34,2% | +0,9 |
| Engenharia | 31,0% | 30,6% | −0,4 |
| Técnico | 24,2% | 23,9% | −0,3 |
| Metodologias Ágeis | 24,1% | 20,0% | −4,1 |
| Inglês | 21,9% | 22,2% | +0,3 |
| Liderança | 20,3% | 21,0% | +0,7 |
| Graduação | 18,9% | 14,3% | −4,6 |
| Administração | 16,3% | 16,8% | +0,5 |

#### Segurança da Informação

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Comunicação | 41,1% | 41,2% | +0,1 |
| **Cloud** | 34,4% | 42,6% | **+8,2** |
| **Organização** | 31,1% | 38,0% | **+6,9** |
| Criatividade | 38,2% | 29,0% | −9,2 |
| Inglês | 30,7% | 30,3% | −0,4 |
| Splunk | 28,4% | 29,8% | +1,4 |
| Engenharia | 27,1% | 30,1% | +3,0 |
| **AWS** | 24,0% | 28,5% | **+4,5** |
| **Azure** | 22,3% | 26,3% | **+4,0** |
| Linux | 26,9% | 16,0% | −10,9 |

#### Testes e Controle de Qualidade

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Engenharia | 29,0% | 36,9% | +7,9 |
| Comunicação | 30,6% | 34,0% | +3,4 |
| Criatividade | 34,2% | 27,0% | −7,2 |
| **Organização** | 25,0% | 34,3% | **+9,3** |
| **Técnico** | 17,6% | 27,1% | **+9,5** |
| Metodologias Ágeis | 26,4% | 15,5% | −10,9 |
| Trabalho em equipe | 20,7% | 16,4% | −4,3 |
| Inglês | 18,3% | 17,3% | −1,0 |
| CI/CD | 22,8% | 12,3% | −10,5 |
| Scrum | 22,2% | 9,1% | −13,1 |

#### Automação de Processos e Sistemas

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Técnico | 43,7% | 46,4% | +2,7 |
| Engenharia | 38,1% | 46,8% | +8,7 |
| Comunicação | 39,4% | 40,4% | +1,0 |
| **Criatividade** | 19,2% | 32,1% | **+12,9** |
| Organização | 20,3% | 28,6% | +8,3 |
| Inglês | 24,3% | 20,4% | −3,9 |
| Python | 20,1% | 16,8% | −3,3 |
| Excel | 10,1% | 17,9% | +7,8 |
| Trabalho em equipe | 14,4% | 11,4% | −3,0 |
| API | 16,4% | 8,2% | −8,2 |

### 3.10 Salários

| Nível | Média 2025 (R$ mil) | Média 2026 (R$ mil) | Δ |
|---|---|---|---|
| Júnior | 3,74 | 2,56 | −1,18 |
| Pleno / Sênior | 7,60 | 6,23 | −1,37 |
| Liderança | 12,71 | 8,33 | −4,38 |
| n/f | 5,73 | 3,32 | −2,41 |

> **Atenção:** valores de 2026 são pontos médios de faixas estimadas. A queda aparente pode refletir viés de seleção e problema de parsing (ver Seção 4).

### 3.11 Inteligência Artificial

| | 2025 | 2026 | Δ pp |
|---|---|---|---|
| Vagas com foco em IA | 7,9% | 24,7% | **+16,8 pp** |

| Área | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Dados e IA | 28,2% | 50,8% | +22,6 |
| Projetos e Gerenciamento | 4,0% | 23,1% | +19,1 |
| Desenvolvimento de Software | 4,5% | 22,4% | +17,9 |
| Segurança da Informação | 2,5% | 18,9% | +16,4 |
| Automação de Processos | 7,6% | 18,9% | +11,3 |
| Infraestrutura e Suporte | 2,0% | 15,2% | +13,2 |
| Testes e CQ | 3,4% | 12,9% | +9,5 |

> A presença de IA triplicou em um ano (7,9% → 24,7%). O crescimento é transversal a todas as áreas, com destaque para áreas antes distantes do tema (Projetos +19,1 pp, Infra +13,2 pp).

### 3.12 Investigação: Queda de Machine Learning

A queda de ML em Dados/IA (28,3% → 21,2%, −7,1 pp) foi investigada no scp_04:

**Decomposição da queda:**
- Queda total de vagas ML: −541 vagas (−40,3%)
- Explicada pela queda de volume geral: −263 vagas (48,6%)
- Queda estrutural (ML menos citado em relação ao total): −278 vagas (51,4%)

> 75,8% da perda absoluta de vagas ML concentra-se na área de Dados e IA.

**Hipótese confirmada — ML absorvido pelo vocabulário de IA:**

| Métrica | 2025 | 2026 |
|---|---|---|
| Vagas com ML + flag IA | 867 (64,6% das vagas ML) | 790 (98,5% das vagas ML) |
| Vagas com ML sem flag IA | 476 (35,4%) | 12 (1,5%) |
| Vagas com IA mas sem ML | 656 | 3.047 |

> Em 2025, 35,4% das vagas com ML não eram classificadas como IA. Em 2026, isso caiu para 1,5%. Ao mesmo tempo, as vagas de IA sem ML saltaram de 656 para 3.047. O sinal é claro: "Machine Learning" tornou-se um termo específico dentro do guarda-chuva "IA" — as empresas migraram para "IA" como rótulo genérico.

---

## 4. Pontos em Aberto

### 4.1 Classificação de Vagas Remotas e Híbridas — RESOLVIDO

**O que foi feito:** o scp_02 detecta modalidade de trabalho pelo texto da descrição da vaga (padrões como `modelo de trabalho remoto`, `100% remoto`, `modelo de trabalho híbrido`), atuando como segunda camada após o match da planilha de localização.

**Resultado:** o scp_02.csv atual reflete corretamente a distribuição — 528 vagas remotas (3,4%) e 940 híbridas (6,1%), totalizando **9,5% de trabalho flexível** — crescimento real sobre os 7,9% de 2025, não queda.

**O que era artefato:** a aparente queda de 7,9% → 0,3% no relatório anterior vinha de um scp_02.csv gerado antes da detecção por texto estar ativa. Com os dados atuais o comparativo mostra o quadro correto.

**Resíduo aceitável:** 40 vagas (0,3%) com `Local Tipo = n/e` e 151 vagas sem estado identificado — volume pequeno, não impacta os resultados gerais.

---

### 4.2 Salário com Baixa Cobertura — ABERTO


**Problema:** apenas 12,9% das vagas têm salário informado. A análise de `scp_analise_softskills` confirma que `scp_02.csv` tem todos os campos `Salario` como `n/f` — o formato do Glassdoor 2026 (`R$ 2.500 (fornecido pela empresa)`) não foi normalizado pela aba `salario` do `criterios.xlsx`, que ainda usa o formato de 2025.

**Impacto:** a análise salarial por nível e área fica incompleta. A queda aparente de salários no comparativo (seção 3.10) pode ser artefato de cobertura.

**Ação necessária:** atualizar a aba `salario` do `criterios.xlsx` com o formato atual, ou substituir o `match_salario` por parsing regex direto.

---

### 4.3 Queda Aparente nos Salários — DEPENDENTE DE 4.2

Os valores de 2026 são estimados por ponto médio de faixa e têm cobertura de 12,9%. Após resolver 4.2, refazer a análise com os dados completos do `scp_02`.

---

### 4.4 R Language em 2025 — RESOLVIDO NOS DADOS DE 2026

O pipeline de 2026 usa padrão restrito (`linguagem r|rstudio|r studio`) e retorna 0,0% corretamente. O artefato de 22% pertence exclusivamente ao pipeline de 2025 e deve ser corrigido lá se necessário.

---

### 4.5 Alto Percentual de Nível "n/f" (20,3%) — ABERTO

20,3% das vagas ficaram sem nível identificado, contra 14,9% em 2025. Provável causa: cargos em inglês não cobertos pelo `criterios.xlsx` (ex: "Staff Engineer", "Principal", "IC4", "Tech Lead"). O `scp_02_chk.xlsx` contém os cargos para análise.

**Ação necessária:** revisar `scp_02_chk.xlsx` e expandir a aba `nivel_cargo` do `criterios.xlsx`.

---

### 4.6 Machine Learning em Queda — INVESTIGADO E RESPONDIDO

A investigação no scp_04 confirma que a queda é real e estrutural: ML tornou-se vocabulário específico dentro de "IA". Não é artefato de cobertura ou sinônimos. Ponto encerrado.

---

### 4.7 Coluna `sk_seguranca_da_info.` no scp_comparativo — NOVO

No output do scp_comparativo (seção de skills por área — Segurança da Informação), aparece `sk_seguranca_da_info.` como nome de skill em vez do label real. Provavelmente erro de normalização do nome de coluna no critérios.xlsx (ponto no nome da skill). Não impacta os dados, mas gera label incorreto no relatório.

**Ação necessária:** verificar o nome da skill correspondente no `criterios.xlsx` e corrigir o caractere especial.

---

### 4.8 SDR / Sales Dev Rep em Desenvolvimento de Software — NOVO

O NLP de títulos de cargo em Desenvolvimento de Software revela que o 5º e o 6º cargos mais frequentes são "SDR - Sales Development Representative" e "Sales Development Representative" — funções comerciais, não técnicas. Isso indica uma falha nos critérios de filtragem ou blacklist para esta área.

**Ação necessária:** avaliar se SDR deve ser movido para outra área ou adicionado à blacklist da aba `palavras_chave`.
