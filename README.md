# Pesquisa de Carreiras em Tecnologia — Brasil

Este repositório reúne o material da pesquisa de carreiras em tecnologia no Brasil: o relatório público, o histórico dos scrapers de 2025 e o pipeline de coleta e análise desenvolvido para 2026.

## Como o repositório está organizado

| Caminho | Conteúdo | Situação |
| --- | --- | --- |
| [`site/`](site/) | Site estático do relatório público e seus assets. | Publicável pelo GitHub Pages. |
| [`webscrapping/`](webscrapping/) | Histórico e pipeline de coleta de vagas do Glassdoor. | Veja o README da pasta. |
| [`webscrapping/versao1/`](webscrapping/versao1/) | Primeira implementação, baseada em Selenium. | Legado de 2025; preservado. |
| [`webscrapping/versao2/`](webscrapping/versao2/) | Segunda implementação, baseada em Playwright. | Trabalho atual; sua autoria. |
| [`webscrapping/versao3/`](webscrapping/versao3/) | Pipeline 2026, dados de apoio e notebooks de análise. | Trabalho atual; pronto para handover. |

## Leitura recomendada para o próximo time

1. Comece pelo [guia do webscrapping](webscrapping/README.md), que explica a separação entre legado e trabalho atual.
2. Leia o [README da versão 3](webscrapping/versao3/README.md) para conhecer o que foi concluído em 2026, os arquivos disponíveis e como reproduzir uma nova rodada.
3. Consulte o [relatório analítico de 2026](webscrapping/versao3/analytics/relatorio_2026.md) para resultados, volumes e metodologia de análise.
4. Antes de iniciar uma nova coleta, siga o [plano de pipeline em máquina única](webscrapping/versao3/docs/plano-pipeline-maquina-unica.md).

## Histórico e responsabilidade

Somente os scripts da versão 1 são o material histórico de **2025**, deixado por **Luana e Tati**, e foram mantidos sem alterações para preservar o contexto. As versões 2 e 3 são seu trabalho e constituem a base atual do repositório.

A versão 3 e sua documentação descrevem o trabalho de **2026**, preparado para ser analisado e continuado por outro time. Dados de coleta, perfis locais do Chrome, ambientes virtuais e credenciais não são versionados.

## Site

O ponto de entrada do relatório é [`site/relatorio-slide-layout.html`](site/relatorio-slide-layout.html). O workflow em [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) publica o conteúdo de `site/` no GitHub Pages.
