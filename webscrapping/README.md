# Webscrapping de vagas

Esta pasta concentra as tentativas e a versão de produção do scraper de vagas do Glassdoor Brasil usado na pesquisa de carreiras em tecnologia.

## Versões

| Pasta | Ano / autoria | Tecnologia | Papel |
| --- | --- | --- | --- |
| [`versao1/`](versao1/) | 2025 — Luana e Tati | Selenium | Primeira abordagem; preservada como histórico. |
| [`versao2/`](versao2/) | 2025 — Luana e Tati | Playwright síncrono | Evolução experimental; preservada como histórico. |
| [`versao3/`](versao3/) | 2026 — trabalho atual | Playwright assíncrono | Pipeline de coleta, enriquecimento e análise. |

## Escopo do handover

As versões 1 e 2 **não foram alteradas** neste trabalho. Elas existem para consulta e comparação técnica; não são o ponto de partida recomendado para uma nova coleta.

A versão 3 é a referência operacional. Ela separa os dados em Bronze (cards coletados), Silver (vagas deduplicadas e enriquecidas) e análise, além de incluir uma estratégia nova para filtrar os títulos antes de enriquecer as páginas individuais. O guia completo está no [README da versão 3](versao3/README.md).

## Dados locais

As pastas `data/`, perfis `chrome-profile-*`, `.session` e `venv/` são locais e ignoradas pelo Git. Portanto, o repositório contém código, critérios, documentação, amostras e notebooks — não a base completa de vagas nem sessões de login.

Para executar qualquer versão, use um perfil Chrome dedicado, faça login manualmente quando solicitado e respeite as regras de uso da plataforma-alvo.
