import asyncio
import csv
from urllib.parse import urlencode, urlparse
from playwright.async_api import async_playwright, Playwright

async def scrape_data(playwright: Playwright):
    # Inicie uma instância do navegador Chromium
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    # Defina a URL base e os parâmetros de consulta para a pesquisa no Glassdoor
    base_url = "https://www.glassdoor.com/Explore/browse-companies.htm?"
    query_params = {
        "overall_rating_low": "3.5",
        "locId": "1132348",
        "locType": "C",
        "locName": "Nova York, NY (EUA)",
        "occ": "Engenheiro de Aprendizado de Máquina",
        "filterType": "RATING_OVERALL",
    }

    # Construa a URL completa com parâmetros de consulta e navegue até ela
    url = f"{base_url}{urlencode(query_params)}"
    await page.goto(url)

    # Abra o arquivo CSV para gravar os dados extraídos
    with open("glassdoor_data.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Empresa", "URL das vagas", "Contagem de vagas", "Contagem de avaliações", "Contagem de salários",
            "Setor", "Localização", "Tamanho global da empresa", "Classificação"
        ])

        # Inicializar um contador para os registros extraídos
        record_count = 0
        while True:
            # Localizar todos os cartões da empresa na página e iterá-los para extrair dados
            company_cards = await page.locator('[data-test="employer-card-single"]').all()
            for card in company_cards:
                try:
                    # Extrair dados relevantes de cada cartão da empresa
                    company_name = await card.locator('[data-test="employer-short-name"]').text_content(timeout=2000) or "N/A"
                    classificação = aguardar cartão.localizador('[data-test="classificação"]').conteúdo_texto(tempo_limite=2000) ou "N/A"
localização = aguardar cartão.localizador('[data-test="localização_empregador"]').conteúdo_texto(tempo_limite=2000) ou "N/A"
                    tamanho_global_da_empresa = aguardar card.locator('[data-test="tamanho-da-empresa"]').text_content(timeout=2000) ou "N/A"
                    setor = aguardar card.locator('[data-test="setor-da-empresa"]').text_content(timeout=2000) ou "N/A"

                    # Construir a URL para listas de empregos
                    jobs_url_path = aguardar card.locator('[data-test="cell-Jobs-url"]').get_attribute("href", timeout=2000) ou "N/A"
                    parsed_url = urlparse(base_url)
                    jobs_url_path = f"{parsed_url.scheme}://{parsed_url.netloc}{jobs_url_path}"

                    # Extrair dados adicionais sobre vagas, avaliações e salários
                    jobs_count = await card.locator('[data-test="cell-Jobs"] h3').text_content(timeout=2000) or "N/A"
                    reviews_count = await card.locator('[data-test="cell-Reviews"] h3').text_content(timeout=2000) or "N/A"
                    salaries_count = await card.locator('[data-test="cell-Salaries"] h3').text_content(timeout=2000) or "N/A"

                    # Grave os dados extraídos no arquivo CSV
                    writer.writerow([
                        company_name, jobs_url_path, jobs_count, reviews_count, salaries_count,
                        industry, location, global_company_size, rating
                    ])

                    record_count += 1
                except Exception as e:
                    print(f"Erro ao extrair dados da empresa: {e}")

            tente:
                # Certifique-se de que o contêiner de paginação esteja visível antes de continuar
                aguarde page.wait_for_selector(".pageContainer", timeout=3000)

                # Identifique o botão "próximo" na página
                botão_próximo = page.locator('[data-test="pagination-next"]')

                # Determine se o botão “próximo” está desativado, não mostrando mais páginas
                is_disabled = await next_button.get_attribute("disabled") is not None
                if is_disabled:
                    break  # Pare se não houver mais páginas para navegar

                # Navegue para a próxima página
                await next_button.click()
                await asyncio.sleep(3)  # Aguarde até que a página carregue completamente
            except Exception as e:
                print(f"Erro ao navegar para a próxima página: {e}")
                break  # Saia do loop em caso de erro de navegação

    print(f"Total de registros extraídos: {record_count}")

    # Fechar o navegador
    await browser.close()

# Ponto de entrada para o script
async def main():
    async with async_playwright() as playwright:
        await scrape_data(playwright)

if __name__ == "__main__":
    asyncio.run(main())