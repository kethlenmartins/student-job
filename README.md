# Pesquisa de Carreiras em Tecnologia no Brasil

Este repositório reúne o material da pesquisa de carreiras em tecnologia no Brasil: o relatório público, o histórico dos scrapers de 2025 e o pipeline de coleta e análise desenvolvido para 2026.

## Como o repositório está organizado

| Caminho | Conteúdo | Situação |
| --- | --- | --- |
| [`site/`](site/) | Site estático do relatório público e recursos associados. | Publicável pelo GitHub Pages. |
| [`webscrapping/`](webscrapping/) | Histórico e pipeline de coleta de vagas do Glassdoor. | Veja o README da pasta. |
| [`webscrapping/versao1/`](webscrapping/versao1/) | Primeira implementação, baseada em Selenium. | Legado de 2025; preservado. |
| [`webscrapping/versao2/`](webscrapping/versao2/) | Segunda implementação, baseada em Playwright. | Implementação atual. |
| [`webscrapping/versao3/`](webscrapping/versao3/) | Pipeline 2026, dados de apoio e notebooks de análise. | Trabalho atual; pronto para handover. |

## Leitura recomendada para o próximo time

1. [Guia do webscrapping](webscrapping/README.md): separação entre legado e trabalho atual.
2. [README da versão 3](webscrapping/versao3/README.md): resultados de 2026, arquivos disponíveis e reprodução de uma nova rodada.
3. [Relatório analítico de 2026](webscrapping/versao3/analytics/relatorio_2026.md): resultados, volumes e metodologia de análise.
4. [Plano de pipeline em máquina única](webscrapping/versao3/docs/plano-pipeline-maquina-unica.md): referência antes de uma nova coleta.

## Histórico e responsabilidade

Somente os scripts da versão 1 são o material histórico de **2025**, deixado por **Luana e Tati**, e foram mantidos sem alterações para preservar o contexto. As versões 2 e 3 constituem a base atual do repositório.

A versão 3 e sua documentação descrevem o trabalho de **2026**, preparado para ser analisado e continuado por outro time. Dados de coleta, perfis locais do Chrome, ambientes virtuais e credenciais não são versionados.

## Site

O ponto de entrada do relatório é [`site/relatorio-slide-layout.html`](site/relatorio-slide-layout.html). O workflow em [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) publica o conteúdo de `site/` no GitHub Pages.
