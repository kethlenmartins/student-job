# Versão 1: Selenium (legado de 2025)

Esta é a primeira implementação do scraper de vagas do Glassdoor. Ela usa **Selenium** conectado a um Chrome aberto com depuração remota.

## Estado e autoria

Os arquivos desta pasta são material histórico de **2025**, deixado por **Luana e Tati**, e foram mantidos intocados. Não é a versão recomendada para uma nova coleta; consulte a [versão 3](../versao3/README.md).

## Arquivos

| Arquivo | Finalidade |
| --- | --- |
| `coleta_glassdoor.py` | Coleta de vagas via Selenium. |
| `iniciar_chrome.sh` | Abre um Chrome com porta de depuração e perfil dedicado. |
| `deteccao_captcha.py` | Utilitários para identificar sinais de CAPTCHA/bloqueio. |
| `testar_deteccao_captcha.py` | Teste controlado para registrar em que etapa ocorre o bloqueio. |
| `palavras-chave-vagas.txt` | Lista de termos de busca. |
| `.env.example` | Exemplo de configuração local. |
| `requirements.txt` | Dependências Python desta versão. |

## Observação de manutenção

O fluxo pressupõe configuração local de Chrome e login manual. Não há garantia de compatibilidade com a interface atual do Glassdoor. Qualquer evolução deve ser feita na versão 3 ou em uma nova versão isolada.
