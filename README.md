# Pesquisa de Carreiras em Tech — webscrapping-2026

Este repositório tem duas partes independentes: o **site** da pesquisa
(publicado via GitHub Pages) e o **scraper** que coleta as vagas do Glassdoor.

---

## Site

**Pasta:** [`site/`](./site/)

Site estático que apresenta os resultados da pesquisa de carreiras em formato
de relatório visual. Publicado automaticamente via GitHub Actions a cada push
na branch principal.

- Layout principal: `site/relatorio-slide-layout.html`
- Inicialização de seções: `site/areas-section-init.js`
- CI/CD: `.github/workflows/deploy-pages.yml`

---

## Webscrapping

**Pasta:** [`webscrapping/`](./webscrapping/)

Scraper que coleta vagas de emprego do Glassdoor Brasil para alimentar a
pesquisa. Organizado em versões evolutivas — a versão ativa é a **versao3**.

| Versão | Status | Tecnologia |
|--------|--------|------------|
| [versao1](./webscrapping/versao1/) | Obsoleta | Selenium |
| [versao2](./webscrapping/versao2/) | Obsoleta | Playwright |
| [versao3](./webscrapping/versao3/) | **Ativa** | Playwright async, multi-máquina |

Para instruções completas de coleta (setup, execução, transferência de dados),
consulte o **[README da versao3](./webscrapping/versao3/README.md)**.
