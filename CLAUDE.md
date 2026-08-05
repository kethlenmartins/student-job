# CLAUDE.md — Pesquisa de Carreiras em Tech 2026

Este arquivo serve como memória de contexto para agentes que trabalhem com qualquer parte deste projeto. Leia antes de modificar qualquer arquivo.

---

## Visão geral do projeto

Pesquisa de carreiras em tecnologia no Brasil, financiada pela Inteli, publicada em parceria com WKS. O objetivo é mapear o mercado de vagas tech: salários, skills, senioridade e distribuição geográfica. A coleta foi feita via webscraping do Glassdoor Brasil (2026); a análise é feita por notebooks ETL.

O projeto tem duas frentes:
- **`webscrapping-2026/`** — scraper + site publicado (GitHub Pages)
- **`webscrapping-2025/`** — pipeline de análise ETL com notebooks Jupyter (legado, base comparativa)

---

## Estado atual (agosto 2026)

**A coleta está concluída.** As três fases do pipeline de dados foram executadas:

1. **Fase 1 (Bronze)** — 9.124 CSVs coletados, ~805.000 registros brutos
2. **Fase 2 (Silver)** — 123.737 vagas únicas em `data/silver/vagas_unicas.csv`
3. **Fase 3 (Enriquecimento)** — 123.161 vagas com descrição (99,5%), 32.758 com salário (26,5%); arquivo final: `data/silver/vagas_enriquecidas.csv`
4. **Analytics** — 15.514 vagas tech classificadas; notebooks scp_01 a scp_04 concluídos

O site está publicado via GitHub Pages. O relatório final está em `webscrapping/versao3/analytics/relatorio_2026.md`.

---

## Arquitetura do scraper — versões

### versao1 — Selenium (obsoleta)
`webscrapping/versao1/coleta_glassdoor.py`

Primeira tentativa. Usou **Selenium** com Chrome em modo "anexar" (conectado a uma instância já aberta pelo script `iniciar_chrome.sh`). Login feito manualmente via "Continuar com Google" (Firebase). Abandonada porque o Selenium é mais facilmente detectado como bot pelo Glassdoor e a sincronização com o Chrome externo era frágil.

### versao2 — Playwright síncrono (obsoleta)
`webscrapping/versao2/coleta_glassdoor.py`

Migração para **Playwright** com sessão persistente em `chrome-profile/`. Melhor que o Selenium, mas ainda síncrono — um terminal por máquina. A limitação de throughput era o problema principal. O arquivo `versao2/tecnicas-antibot.md` documenta as 12 técnicas antibot estudadas nessa fase (rotação de IP, TLS fingerprinting, headers realistas, stealth plugins, backoff exponencial etc.).

### versao3 — Playwright async, multi-máquina (ATIVA)
`webscrapping/versao3/`

Versão de produção. Principais diferenças em relação às anteriores:

- **Async Playwright** com múltiplos contextos de browser em paralelo
- **16 perfis Chrome distintos** (pastas `profiles/chrome-profile-e1` a `e16`), um por terminal, cada um com sessão de login persistida em `.session`
- **Distribuição em 4 máquinas** coordenadas manualmente via Slack/Drive
- **Delays gaussianos** (`numpy.random.normal`) para simular comportamento humano
- **Retomada segura**: scripts verificam progresso existente antes de começar

---

## Estrutura de arquivos — versao3

```
webscrapping/versao3/
├── coleta_glassdoor.py      # Fase 1: coleta (Bronze)
├── deduplicar.py            # Fase 2: dedup (Bronze → Silver)
├── enriquecer.py            # Fase 3: enriquecimento por URL
├── mesclar.py               # Fase 3 final: merge de todos os enriquecidos
├── fix_salario.py           # Utilitário: atualiza parsing de salário no notebook
├── fix_scp03.py             # Utilitário: atualiza extração de skills no scp_03
├── palavras-chave-vagas.txt # ~260 palavras-chave de busca (lista Python)
├── criterios-2026.xlsx      # Planilha de critérios de classificação (8 abas)
├── requirements.txt         # numpy, pandas, playwright, python-dotenv
├── data/
│   ├── bronze/              # CSVs brutos por keyword×UF (~9.124 arquivos)
│   ├── silver/              # Deduplicado + enriquecido
│   └── gold/                # Reservado para agregações futuras
└── analytics/
    ├── relatorio_2026.md    # Relatório final com todos os resultados
    ├── scp_01.ipynb         # Filtragem: vagas → vagas tech
    ├── scp_02.ipynb         # Classificação: área, nível, local
    ├── scp_03.ipynb         # Extração de 134 skills (one-hot)
    ├── scp_04.ipynb         # NLP dos títulos de cargos
    └── amostra/             # Amostras para validação manual
```

---

## Pipeline de dados (medalhão)

```
coleta_glassdoor.py           deduplicar.py           enriquecer.py + mesclar.py
  8 máquinas × 2 terminais  →  só Kethlen roda   →    16 terminais paralelos
  Bronze: ~805k registros       Silver: 123.737         Silver: vagas_enriquecidas.csv
                                vagas únicas
                                    ↓
                         scp_01 → scp_02 → scp_03 → scp_04
                         15.869   15.514   15.514×141  NLP
                         vagas    vagas    cols skills  cargos
```

### Fase 1 — coleta_glassdoor.py

Busca keyword × UF no Glassdoor Brasil. Args CLI:
```
--kw-inicio INT      índice de início nas palavras-chave
--kw-fim INT         índice de fim
--perfil STR         nome da pasta do perfil Chrome (ex: chrome-profile-e1)
--sem-enriquecer     pula enriquecimento (sempre usar na Fase 1)
--assume-logged-in   usa sessão existente sem prompt de login
--ufs SP,RJ,...      filtra por estados
```

Output: `data/bronze/{keyword}_{UF}.csv`  
Colunas: `Função, Localização, Empresa, Data de Publicacao, Média Salarial, URL, Skills Necessarias`  
(`Skills Necessarias` inicia como "NF" — preenchido na Fase 3)

### Fase 2 — deduplicar.py

Roda **somente na máquina da Kethlen (M1)**. Lê todos os CSVs de `data/bronze/`, remove duplicatas por:
1. `jobListingId` extraído da URL (ID canônico do Glassdoor)
2. Hash de `Funcao + Empresa + Localização` normalizado (fallback)

Output: `data/silver/vagas_unicas.csv` (123.737 linhas)  
Side-effect: imprime os intervalos de índice para distribuir a Fase 3 entre 16 terminais.

### Fase 3 — enriquecer.py

Cada terminal recebe uma fatia de `vagas_unicas.csv` via `--inicio / --fim`. Visita cada URL e extrai a descrição completa. Checkpoint a cada 50 linhas (retomada segura).  
Output: `data/silver/enriquecido_{inicio}_{fim}.csv`

**mesclar.py** consolida todos os `enriquecido_*.csv` em `data/silver/vagas_enriquecidas.csv`.

---

## Distribuição multi-máquina

| Máquina | Pessoa | OS | Fase 1 | Fase 3 |
|---------|--------|----|--------|--------|
| M1 ⭐ central | MacBook Kethlen | macOS | t1, t2 | e1–e4 |
| M2 | PC Inteli Kethlen | Linux | t3, t4 | e5–e8 |
| M3 | PC Inteli Marco | Linux | — | e9–e12 |
| M4 | Leo | Windows | — | e13–e16 |

Coordenação: CSVs trafegam via Slack/Google Drive. M1 é o nó central (deduplicação + merge final).

Execução em background:
- macOS/Linux: `tmux` + `caffeinate -i` para evitar sleep
- Windows: PowerShell com suspensão desativada

---

## Pipeline de análise (notebooks)

Localização: `webscrapping/versao3/analytics/`  
Entrada base: `data/silver/vagas_enriquecidas.csv`

| Notebook | Função | Saída | Registros |
|----------|--------|-------|-----------|
| scp_01 | Filtra vagas tech por palavras-chave de cargo | scp_01.csv | 15.869 |
| scp_02 | Classifica área/nível/tipo/local; aplica blacklist | scp_02_clean.xlsx | 15.514 |
| scp_03 | Extrai 134 skills (one-hot) + flag IA | scp_03.csv (141 colunas) | 15.514 |
| scp_04 | NLP de n-gramas em títulos de cargos | análises | — |

**criterios-2026.xlsx** controla toda a classificação. Abas principais:
- `palavras_chave` — termos que qualificam uma vaga como tech
- `tipo_cargo / nivel_cargo` — regras de senioridade
- `cidades / salario` — normalização geográfica
- `skills` — catálogo de skills com sinônimos (usado no scp_03)
- `blacklist` — termos de exclusão
- `IA` — palavras-chave para flag de IA

---

## Antibot — estratégias em uso (versao3)

O Glassdoor detecta scrapers por fingerprinting TLS, comportamento de sessão e padrões de requisição. A versao3 usa:

- **Chrome real não-headless** com perfis persistentes (evita `navigator.webdriver = true`)
- **Sessão de login Google/Firebase** salva por perfil (evita CAPTCHA de login repetido)
- **Delays gaussianos** via `numpy.random.normal` (média ~4s, desvio ~1.5s)
- **Scroll simulado** antes de extrair dados das páginas
- **Fechamento automático de popups** (cookie banners, modais de cadastro)
- **Backoff exponencial** após 5 falhas consecutivas
- **Pausa manual** quando CAPTCHA é detectado (input() interativo)

---

## Site (GitHub Pages)

```
site/
├── relatorio-slide-layout.html   # página principal (deploy como index.html)
├── areas-section-init.js         # inicialização dos gráficos interativos
├── *.png                         # assets gráficos
└── fonts/                        # Platypi, Azurio, Manrope
```

Deploy automático via `.github/workflows/deploy-pages.yml` a cada push em main.

---

## Resultados principais (2026)

Fonte: `analytics/relatorio_2026.md` (gerado em 29/07/2026)

- **15.514 vagas tech** classificadas
- **Área dominante**: Desenvolvimento de Software (30,7%), seguido de Projetos/Gerenciamento (21,6%) e Infra/Suporte (20,5%)
- **Senioridade**: 47,4% Pleno/Sênior, 22,1% Júnior, 10,1% Liderança
- **Top hard skills**: Cloud (18,5%), SQL (18,2%), Metodologias Ágeis (17,4%), Python (15,4%)
- **Top soft skill**: Comunicação (41,6%)
- **IA mencionada**: 3.837 vagas (24,7%); vagas com IA concentram o dobro de salários acima de R$ 10k
- **Inglês**: 18,7% das vagas; amplifica acesso a faixas salariais de R$ 5k–10k
- **Concentração geográfica**: SP (39,7%), MG (9,6%), RJ (6,8%)

---

## Comparativo com 2025

O pipeline de análise 2025 está em `webscrapping-2025/Códigos Webscrapping Recente/` (notebooks scp_01 a scp_04). A fonte de dados de 2025 combinou Glassdoor + Kadoa. O comparativo entre anos está referenciado no relatório 2026 como "Pipeline Paulo".

---

## Textos do relatório público

`docs/textos.md` contém os textos editoriais dos 3 capítulos do relatório final (Panorama do Mercado, Carreira e Progressão, Áreas e Posicionamento). Esses textos são usados no site publicado.

---

## Setup de desenvolvimento (versao3)

```bash
cd webscrapping/versao3
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# ou: venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
playwright install chrome
```

Python 3.10+. O venv e os perfis Chrome não são versionados (`.gitignore`).
