# Versão 2 — Playwright (legado de 2025)

Esta pasta registra a evolução do scraper para **Playwright**. Ela introduz perfil persistente do Chrome e coleta de cards por palavra-chave e UF, mas permanece uma implementação experimental/síncrona anterior ao pipeline de 2026.

## Estado e autoria

Os scripts são material histórico de **2025**, deixado por **Luana e Tati**, e foram preservados sem alterações. Para a coleta e análise atuais, consulte a [versão 3](../versao3/README.md).

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
