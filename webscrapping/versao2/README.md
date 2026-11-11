# Versão 2 — Playwright

Esta pasta registra a evolução do scraper para **Playwright**. Ela introduz perfil persistente do Chrome e coleta de cards por palavra-chave e UF, em uma implementação síncrona anterior à versão 3.

## Estado e autoria

Esta versão é de sua autoria. Ela registra uma etapa importante da evolução técnica antes do pipeline assíncrono da [versão 3](../versao3/README.md), que é a referência recomendada para novas coletas.

## Arquivos

| Arquivo | Finalidade |
| --- | --- |
| `coleta_glassdoor.py` | Coleta Bronze com Playwright e perfil persistente. |
| `glassdoor-scrapper.py` | Protótipo de coleta de dados de empresas. |
| `pagination.py` | Trecho experimental de paginação. |
| `iniciar_chrome.sh` | Utilitário de Chrome com depuração remota. |
| `palavras-chave-vagas.txt` | Lista de termos de busca. |
| `tecnicas-antibot.md` | Anotações de pesquisa sobre mecanismos anti-bot. |
| `requirements.txt` | Dependências Python desta versão. |

## Observação de manutenção

Os seletores e o comportamento do Glassdoor mudam com frequência; este código não deve ser assumido como operacional sem validação. A estratégia atual e auditável está documentada na versão 3.
