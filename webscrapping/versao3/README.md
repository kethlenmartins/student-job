# Versão 3 — Pipeline de vagas Glassdoor 2026

Esta é a implementação de 2026 para coleta e análise de vagas de tecnologia no Brasil. Ela é a referência para o próximo time: reúne o pipeline executado, os critérios de classificação, os notebooks e o plano para uma nova rodada mais econômica.

> A versão 1 é o legado de 2025 deixado por Luana e Tati e mantido sem alteração. As versões 2 e 3 são seu trabalho; esta pasta contém o pipeline de 2026.

## O que já foi concluído

A rodada histórica de 2026 foi concluída em fluxo distribuído. Seus resultados consolidados são:

| Etapa | Resultado |
| --- | ---: |
| Bronze — arquivos de coleta | 9.124 CSVs / cerca de 805 mil registros brutos |
| Silver — vagas únicas | 123.737 vagas |
| Enriquecimento — descrições obtidas | 123.161 vagas (99,5%) |
| Enriquecimento — salário informado | 32.758 vagas (26,5%) |
| Base tech classificada | 15.514 vagas |

O detalhamento dos resultados e da metodologia está em [`analytics/relatorio_2026.md`](analytics/relatorio_2026.md).

## Estrutura da pasta

| Caminho | Conteúdo |
| --- | --- |
| `coleta_glassdoor.py` | Coleta de cards do Glassdoor para a camada Bronze. |
| `deduplicar.py` | Consolida a Bronze e gera `vagas_unicas.csv` na Silver. |
| `filtrar_tech.py` | Separa vagas `tech`, `ambigua` e `nao_tech` pelo título antes do enriquecimento. |
| `enriquecer_paralelo.py` | Enriquecimento recomendado: um Chrome e poucas abas, com persistência incremental. |
| `enriquecer.py` | Enriquecimento legado por fatia; usado na rodada distribuída anterior. |
| `mesclar.py` | Consolida os arquivos `enriquecido_*.csv`. |
| `analytics/` | Notebooks, relatório final e amostras de validação. |
| `criterios-2026.xlsx` | Regras de cargo, blacklist, senioridade, localidade, salário e skills. |
| `docs/plano-pipeline-maquina-unica.md` | Plano técnico e critérios de aceite para a próxima rodada. |
| `gerar_amostras.py`, `gerar_amostra_llms.py` | Geração de amostras para revisão manual. |
| `fix_salario.py`, `fix_scp03.py`, `add_llm_cells.py` | Utilitários pontuais para notebooks e análise. |

Os dados completos não estão no Git: `data/`, perfis Chrome e `venv/` são artefatos locais ignorados.

## Pipeline executado em 2026

```text
coleta_glassdoor.py → Bronze (cards por palavra-chave × UF)
  → deduplicar.py → Silver (vagas_unicas.csv)
  → enriquecer.py → Silver (descrições por URL)
  → mesclar.py → vagas_enriquecidas.csv
  → analytics/scp_01.ipynb até scp_04.ipynb → análises e relatório
```

A rodada original usou várias máquinas e perfis Chrome. Essa operação está encerrada; os scripts continuam disponíveis para referência e para processar uma base já distribuída.

## Próxima rodada: fluxo recomendado

Para não visitar páginas de vagas que não pertencem ao recorte tech, a próxima rodada deve classificar o título **antes** do enriquecimento:

```text
Bronze → deduplicação → triagem por título → fila tech → enriquecimento → análise
                              ├─ fila ambigua (auditoria)
                              └─ fila nao_tech (arquivamento)
```

O plano completo, incluindo justificativa, recuperação de falhas e critérios de aceite, está em [`docs/plano-pipeline-maquina-unica.md`](docs/plano-pipeline-maquina-unica.md).

### Preparação local

Requer Python 3.10+ e Google Chrome instalado.

```bash
cd webscrapping/versao3
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chrome
```

No Windows, ative com `venv\Scripts\Activate.ps1`. Use um perfil Chrome exclusivo por processo; na primeira execução, não use `--assume-logged-in` e faça o login manualmente.

### Exemplo de execução isolada

Use `--run-id` para não sobrescrever a coleta histórica. O identificador cria `data/runs/<id>/` com as camadas Bronze, Silver e Gold.

```bash
# Piloto: uma keyword em SP e RJ
python coleta_glassdoor.py --run-id 2026-nova --kw-inicio 0 --kw-fim 1 \
  --ufs SP,RJ --perfil chrome-profile-coleta --sem-enriquecer

# Bronze → Silver e triagem auditável
python deduplicar.py --run-id 2026-nova
python filtrar_tech.py \
  --input-file data/runs/2026-nova/silver/vagas_unicas.csv

# Enriquecimento somente da fila tech
python enriquecer_paralelo.py \
  --input-file data/runs/2026-nova/silver/fila_tech.csv \
  --perfil chrome-profile-enrich --workers 2 --assume-logged-in

# Consolidação
python mesclar.py --run-id 2026-nova
```

Comece com duas abas (`--workers 2`); o máximo aceito pelo script é quatro. Não compartilhe o mesmo perfil Chrome entre processos e não misture resultados de `enriquecer.py` e `enriquecer_paralelo.py` para a mesma fatia.

## Análise

Os notebooks em `analytics/` usam `vagas_enriquecidas.csv` como base e seguem esta sequência:

| Notebook | Papel |
| --- | --- |
| `scp_01.ipynb` | Seleciona vagas tech pelos termos de cargo. |
| `scp_02.ipynb` | Classifica área, nível, tipo e localidade; aplica limpeza. |
| `scp_03.ipynb` | Extrai skills e a sinalização de IA. |
| `scp_04.ipynb` | Analisa títulos e n-gramas. |
| `scp_analise_softskills.ipynb` | Apoia a validação de soft skills. |
| `scp_comparativo.ipynb` | Compara resultados de 2025 e 2026. |

`criterios-2026.xlsx` é a fonte de regras. Alterações de recorte devem ser feitas e versionadas nessa planilha, depois validadas por amostra; a triagem grava os termos encontrados e o hash do arquivo para manter rastreabilidade.
