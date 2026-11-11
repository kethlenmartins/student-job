# Webscrapping de vagas

Esta pasta concentra as tentativas e a versão de produção do scraper de vagas do Glassdoor Brasil usado na pesquisa de carreiras em tecnologia.

## Versões

| Pasta | Ano / autoria | Tecnologia | Papel |
| --- | --- | --- | --- |
| [`versao1/`](versao1/) | 2025, Luana e Tati | Selenium | Primeira abordagem; preservada como histórico. |
| [`versao2/`](versao2/) | Trabalho atual | Playwright síncrono | Evolução do scraper. |
| [`versao3/`](versao3/) | 2026, trabalho atual | Playwright assíncrono | Pipeline de coleta, enriquecimento e análise. |

## Escopo do handover

Somente a versão 1 é material histórico preservado. As versões 2 e 3 compõem a implementação atual; a versão 3 é a referência operacional para uma nova rodada.

A versão 3 é a referência operacional. Ela separa os dados em Bronze (cards coletados), Silver (vagas deduplicadas e enriquecidas) e análise, além de incluir uma estratégia nova para filtrar os títulos antes de enriquecer as páginas individuais. O guia completo está no [README da versão 3](versao3/README.md).

## Dados locais

As pastas `data/`, perfis `chrome-profile-*`, `.session` e `venv/` são locais e ignoradas pelo Git. Portanto, o repositório contém código, critérios, documentação, amostras e notebooks, mas não a base completa de vagas nem sessões de login.

A execução de qualquer versão requer um perfil Chrome dedicado, login manual quando solicitado e respeito às regras de uso da plataforma-alvo.
