# Relatório de Mercado Tech Brasil — 2026

**Data de geração:** 29/07/2026  
**Fonte:** Glassdoor Brasil, coleta distribuída multi-máquina (versao3)  
**Comparativo:** Pipeline Paulo — Glassdoor Brasil 2025

---

## 1. Pipeline de Dados

### 1.1 Bronze — Coleta

O scraper rodou em modo distribuído, com múltiplas máquinas buscando simultaneamente no Glassdoor Brasil. Cada máquina varreu combinações de **palavra-chave × UF**, gerando um arquivo CSV por combinação (ex: `informacao_SP.csv`, `analista_de_dados_MG.csv`).

- **9.124 arquivos CSV** coletados na camada bronze  
- **~805.000 registros brutos** (com duplicatas entre UFs, máquinas e datas de coleta)  
- Colunas brutas: Função, Localização, Empresa, Data de Publicação, URL

### 1.2 Silver — Deduplicação e Enriquecimento

**`deduplicar.py`** consolidou todos os CSVs bronze, removendo registros duplicados por URL/combinação de campos-chave.

**`enriquecer.py`** acessou a página de cada vaga e usou um LLM (Claude) para extrair campos estruturados:
- Descrição completa da vaga (`Skills Necessarias`)
- Salário médio (`Média Salarial`)

Resultado após deduplicação e enriquecimento:

| Etapa | Registros |
|---|---|
| Bronze (bruto) | ~805.000 |
| Silver — vagas únicas | 123.737 |
| Silver — com descrição enriquecida (>50 chars) | 123.161 (99,5%) |
| Silver — com salário informado | 32.758 (26,5%) |

O arquivo consolidado final é `data/silver/vagas_enriquecidas.csv`.

### 1.3 Analytics — Filtragem e Classificação

A partir do silver, quatro notebooks ETL rodaram em sequência:

**`scp_01.ipynb`** — Filtragem para vagas tech  
Carrega `vagas_enriquecidas.csv`, normaliza colunas, e filtra apenas cargos que contenham palavras-chave tech (ex: "desenvolvedor", "dados", "infraestrutura").  
→ **15.869 vagas tech**

**`scp_02.ipynb`** — Classificação e limpeza  
Classifica cada vaga em Área, Tipo, Nível e Local via correspondência com a planilha `criterios.xlsx`. Remove vagas com termos da blacklist.  
→ **15.514 vagas** (−355 pela blacklist)

**`scp_03.ipynb`** — Extração de skills  
Para cada skill do catálogo (134 skills: hard, soft, idiomas, formação), busca presença na descrição usando `clean_text_search` (remoção de pontuação + `\b` word boundaries) com expansão por sinônimos da planilha de critérios.  
Detecta também flag `IA` via lista de palavras-chave (ex: llm, chatgpt, generativ).  
→ **matriz 15.514 × 141 colunas**

**`scp_04.ipynb`** — Análise NLP de cargos  
Análise de n-gramas e frequência de termos nos títulos de cargos, por área.

---

## 2. Panorama 2026

### 2.1 Volume de Vagas

**15.514 vagas tech** classificadas após filtragem.

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

**Modalidade de trabalho:** 99,7% presencial/nacional, 0,3% remoto classificado  
*(Nota: a classificação de vagas remotas tem limitações — ver Seção 4)*

### 2.5 Hard Skills

Top 20, por frequência de menção nas descrições de vagas:

| Rank | Skill | Vagas | % |
|---|---|---|---|
| 1 | Cloud | 2.877 | 18,5% |
| 2 | SQL | 2.825 | 18,2% |
| 3 | Metodologias Ágeis | 2.704 | 17,4% |
| 4 | Python | 2.393 | 15,4% |
| 5 | API | 2.256 | 14,5% |
| 6 | Excel | 2.033 | 13,1% |
| 7 | AWS | 2.137 | 13,8% |
| 8 | CI/CD | 1.812 | 11,7% |
| 9 | Office 365 | 1.428 | 9,2% |
| 10 | Git | 1.645 | 10,6% |
| 11 | Azure | 1.628 | 10,5% |
| 12 | Scrum | 1.194 | 7,7% |
| 13 | Java | 1.225 | 7,9% |
| 14 | Power BI | 1.252 | 8,1% |
| 15 | Windows | 1.004 | 6,5% |
| 16 | Docker | 1.158 | 7,5% |
| 17 | Linux | 960 | 6,2% |
| 18 | JavaScript | 1.377 | 8,9% |
| 19 | React | 868 | 5,6% |
| 20 | Kanban | 810 | 5,2% |

### 2.6 Soft Skills

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

### 2.7 Idiomas

| Idioma | Vagas | % |
|---|---|---|
| Inglês | 2.901 | 18,7% |
| Espanhol | 557 | 3,6% |
| Francês | 64 | 0,4% |
| Alemão | 62 | 0,4% |
| Italiano | 14 | 0,1% |

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

### 2.9 Salários

**2.043 vagas com salário informado (12,9%)**  
*(Nota: dado subestimado — ver Seção 4)*

Distribuição por faixa (vagas com salário informado):

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

---

## 3. Comparativo 2025 vs 2026

**Base de comparação:** Pipeline Paulo 2025 (Glassdoor Brasil) vs Pipeline versao3 2026 (Glassdoor Brasil)  
**Metodologia de skills:** ambos os anos usam correspondência com `\b` word boundaries + expansão por sinônimos da planilha de critérios.

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

> Destaque: Projetos e Gerenciamento cresceu 7,6 pp, enquanto Desenvolvimento caiu 5,6 pp.

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
| Santa Catarina | 5,3% | 6,2% | +0,9 |
| Paraná | 6,8% | 6,8% | 0,0 |
| Rio Grande do Sul | 6,3% | 5,4% | −0,9 |

> São Paulo concentrou +13,1 pp do mercado. As categorias "n/e" e "Trabalho Remoto" somavam 24,3% em 2025 e não aparecem em 2026 — parte desse volume pode ter sido reclassificada para estados (ver Seção 4).

### 3.5 Modalidade de Trabalho

| Modalidade | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Nacional / Presencial | 92,1% | 99,7% | +7,6 |
| Remoto | 7,9% | 0,3% | −7,6 |

> **Atenção:** a queda do remoto é provavelmente um artefato de classificação, não uma tendência real de mercado — ver Seção 4.

### 3.6 Hard Skills

| Rank | Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|---|
| 1 | SQL | 21,2% | 18,2% | −3,0 |
| 2 | Cloud | 19,4% | 18,5% | −0,9 |
| 3 | Metodologias Ágeis | 20,0% | 17,4% | −2,6 |
| 4 | Python | 18,3% | 15,4% | −2,9 |
| 5 | API | 14,8% | 14,5% | −0,3 |
| 6 | AWS | 14,9% | 13,8% | −1,1 |
| 7 | **CI/CD** | 13,0% | 11,7% | −1,3 |
| 8 | Git | 13,0% | 10,6% | −2,4 |
| 9 | **Excel** | 9,8% | 13,1% | **+3,3** |
| 10 | JavaScript | 13,2% | 8,9% | −4,3 |
| 11 | Azure | 11,5% | 10,5% | −1,0 |
| 12 | R *(¹)* | 22,0% | 0,0% | — |
| 13 | Scrum | 11,9% | 7,7% | −4,2 |
| 14 | Office 365 | 9,4% | 9,2% | −0,2 |
| 15 | Java | 9,1% | 7,9% | −1,2 |
| 16 | Power BI | 7,8% | 8,1% | +0,3 |
| 17 | Docker | 7,9% | 7,5% | −0,4 |
| 18 | Linux | 9,2% | 6,2% | −3,0 |
| 19 | React | 7,9% | 5,6% | −2,3 |
| 20 | Kanban | 7,8% | 5,2% | −2,6 |

> *(¹) R language: o valor de 22% em 2025 é um artefato do pipeline daquele ano (padrão `\b(r)\b` capturava a letra "r" isolada após remoção de pontuação). O valor real de 2025 também deve ser próximo de 0%.*

> **Destaques:** Excel subiu +3,3 pp. Todas as outras skills caíram levemente, indicando que o mercado está exigindo um portfólio mais diversificado em vez de skills isoladas muito dominantes.

### 3.7 Soft Skills

| Skill | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Comunicação | 36,9% | 41,6% | **+4,7** |
| Criatividade / Inovação | 31,3% | 30,1% | −1,2 |
| **Organização** | 26,7% | 34,4% | **+7,7** |
| Trabalho em equipe | 20,1% | 15,9% | −4,2 |
| **Liderança** | 13,5% | 17,0% | **+3,5** |
| Resolução de problemas | 14,1% | 14,5% | +0,4 |
| **Autonomia** | 7,8% | 10,3% | **+2,5** |
| Proatividade | 10,3% | 9,9% | −0,4 |
| Pensamento analítico | 10,2% | 8,8% | −1,4 |
| Adaptabilidade | 6,8% | 5,5% | −1,3 |

> Tendência clara: soft skills de **autogestão** (Organização +7,7 pp, Autonomia +2,5 pp, Liderança +3,5 pp) cresceram, enquanto skills de **colaboração passiva** (Trabalho em equipe −4,2 pp) caíram.

### 3.8 Idiomas

| Idioma | 2025 (%) | 2026 (%) | Δ pp |
|---|---|---|---|
| Inglês | 19,0% | 18,7% | −0,3 |
| Espanhol | 3,2% | 3,6% | +0,4 |
| Francês | 0,4% | 0,4% | 0,0 |
| Alemão | 0,4% | 0,4% | 0,0 |

> Inglês praticamente estável. Demanda de idiomas não sofreu alteração relevante entre os anos.

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

> **Atenção:** valores de 2026 são pontos médios de faixas estimadas (ex: "R$ 2k–R$ 5k" → ponto médio R$ 3.5k), com apenas 12,9% das vagas com salário informado. A queda aparente pode refletir viés de seleção mais do que tendência real de mercado — ver Seção 4.

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

> Este é o resultado mais robusto do comparativo: IA triplicou sua presença no mercado tech em um ano, de 7,9% para 24,7%. O crescimento é transversal a todas as áreas.

---

## 4. Pontos a Investigar

### 4.1 Classificação de Vagas Remotas

**Problema:** Em 2025, o Glassdoor retornava "Trabalho Remoto" como string de localização, que o classificador mapeava direto para `Local Tipo = remoto` (7,9% das vagas). Em 2026, as strings de localização chegam em formato diferente (ex: "São Paulo, SP - Híbrido", "Brasil") e não casam com a entrada "Trabalho Remoto" no `criterios.xlsx`.

**Impacto:** A queda 7,9% → 0,3% de vagas remotas **não reflete o mercado real**. Os 4,1% de `n/f` em Local Estado provavelmente incluem vagas remotas não classificadas.

**Ação necessária:** Atualizar a aba `cidades` do `criterios.xlsx` com as novas strings de localização que o scraper de 2026 retorna para vagas remotas/híbridas.

---

### 4.2 Salário com Baixa Cobertura

**Problema:** Apenas 12,9% das vagas (2.043) têm salário informado em 2026. A coluna `Salario` na `scp_02` está toda como `n/f` porque a aba `salario` do `criterios.xlsx` foi mantida no formato do pipeline de 2025 (`R$ 1 mil`, `R$ 2 mil`…) enquanto o scraper de 2026 retorna o formato do Glassdoor (`R$ 2.500 (fornecido pela empresa)`).

**Impacto:** A análise salarial usa os dados brutos de `scp_01.csv` via regex como contorno, mas perde a integração com nível/área que vem do `scp_02`.

**Ação necessária:** Atualizar a aba `salario` do `criterios.xlsx` com os valores no formato `R$ X.XXX (fornecido pela empresa)`, ou substituir o `match_salario` no `scp_02` por uma função regex equivalente à do comparativo.

---

### 4.3 Queda Aparente nos Salários

**Problema:** O comparativo de salários por nível mostra quedas em todos os níveis (Liderança: 12,71 → 8,33 R$ mil). Os dados de 2026 são baseados em pontos médios de faixas (ex: faixa "R$ 2k–R$ 5k" → 3,5k), e os de 2025 em uma análise mais detalhada da distribuição real. A combinação de viés de cobertura (12,9% das vagas) com o método de ponto médio pode distorcer a comparação.

**Ação necessária:** Após corrigir o item 4.2, refazer a análise salarial com os dados completos do `scp_02`.

---

### 4.4 R Language em 2025 (Artefato Confirmado)

**Problema:** O valor de 22% para R language em 2025 é um bug do pipeline daquele ano: o padrão `\b(r)\b` capturava a letra "r" isolada após a remoção de pontuação (ex: "c/r" → "c r", onde o "r" solto casava). O valor corrigido de 2026 (0,0%) é preciso.

**Impacto:** O comparativo mostra "R: 22,0% → 0,0%, −22 pp" que é enganoso. O verdadeiro delta é próximo de zero.

**Ação necessária:** Corrigir o `scp_03.ipynb` de 2025 aplicando a mesma regra especial do R que foi implementada em 2026 (padrão restrito a `linguagem r|rstudio|r studio`). Requer re-executar o pipeline de 2025.

---

### 4.5 Alto Percentual de Nível "n/f"

**Problema:** 20,3% das vagas de 2026 ficaram com Nível = `n/f` (não encontrado), contra 14,9% em 2025. Isso pode indicar que a aba `nivel_cargo` do `criterios.xlsx` não cobre nomenclaturas novas de cargo que aparecem em 2026 (ex: cargos com termos em inglês como "Staff Engineer", "Principal", "IC4").

**Ação necessária:** Analisar os Cargos com `n/f` no arquivo `scp_02_chk.xlsx` e expandir o `criterios.xlsx` com as novas nomenclaturas.

---

### 4.6 Machine Learning em Queda na Área de Dados (−7,1 pp)

**Observação:** A queda de Machine Learning de 28,3% para 21,2% na área de Dados pode ser real (substituição pelo vocabulário de IA Generativa — LLMs, RAG, embeddings) ou pode ser parcialmente explicada por uma cobertura diferente de sinônimos entre os anos. Merece investigação qualitativa nas descrições das vagas.

---
