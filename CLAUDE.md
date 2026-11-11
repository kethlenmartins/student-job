# Contexto técnico: Pesquisa de Carreiras em Tecnologia 2026

Este arquivo é a referência técnica rápida do repositório. A documentação para continuidade do projeto está nos READMEs da raiz, de `webscrapping/` e de `webscrapping/versao3/`.

## Escopo e responsabilidade

- `webscrapping/versao1/` é o script histórico de **2025**, deixado por **Luana e Tati**. Está preservado e não deve ser alterado incidentalmente.
- `webscrapping/versao2/` e `webscrapping/versao3/` compõem a implementação atual; a versão 3 é a referência para evolução do pipeline.
- `site/` contém o relatório público estático, publicado pelo workflow de GitHub Pages em `.github/workflows/deploy-pages.yml`.

## Estado da rodada 2026

A coleta distribuída foi concluída. Os totais registrados em `webscrapping/versao3/analytics/relatorio_2026.md` são:

| Camada | Resultado |
| --- | ---: |
| Bronze | 9.124 CSVs e cerca de 805 mil registros brutos |
| Silver deduplicada | 123.737 vagas únicas |
| Descrições enriquecidas | 123.161 vagas (99,5%) |
| Base tech analisada | 15.514 vagas |

Os dados completos e as sessões de navegador são locais e ignorados pelo Git. Não presuma que `data/` esteja disponível em um clone novo.

## Pipeline 2026

```text
coleta_glassdoor.py → Bronze
deduplicar.py → Silver / vagas_unicas.csv
filtrar_tech.py → filas tech, ambigua e nao_tech
enriquecer_paralelo.py → descrições incrementais
mesclar.py → vagas_enriquecidas.csv
analytics/scp_01.ipynb ... scp_04.ipynb → relatório
```

O fluxo distribuído original usou `enriquecer.py`; em uma nova rodada, prefira `filtrar_tech.py` antes do enriquecimento e `enriquecer_paralelo.py` com um único Chrome e duas abas inicialmente. O plano operacional completo está em `webscrapping/versao3/docs/plano-pipeline-maquina-unica.md`.

## Convenções importantes

- A execução de `coleta_glassdoor.py`, `deduplicar.py` e `mesclar.py` deve usar `--run-id` para isolar uma rodada em `webscrapping/versao3/data/runs/<id>/` e não sobrescrever dados históricos.
- A triagem usa `criterios-2026.xlsx`; ela registra termos encontrados e o hash da planilha, portanto mudanças de regra devem ocorrer ali e ser validadas por amostra.
- Não compartilhe um diretório `chrome-profile-*` entre processos. Na primeira abertura de um perfil, permita o login manual; somente depois use `--assume-logged-in`.
- Não misture saídas de `enriquecer.py` e `enriquecer_paralelo.py` na mesma fatia de entrada.
- Perfis Chrome, ambientes virtuais, credenciais e dados de coleta permanecem fora do controle de versão.

## Análise

`analytics/scp_01.ipynb` filtra cargos tech; `scp_02.ipynb` classifica área, nível e localidade; `scp_03.ipynb` extrai skills e sinalização de IA; `scp_04.ipynb` analisa títulos. `scp_comparativo.ipynb` contém a comparação 2025 × 2026.
