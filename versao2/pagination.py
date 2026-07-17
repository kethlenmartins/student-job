while True:
    # Certifique-se de que o contêiner de paginação esteja visível antes de continuar
    await page.wait_for_selector(".pageContainer", timeout=3000)

    # Identifique o botão “Próximo” na página
    next_button = page.locator('[data-test="pagination-next"]')

    # Determine se o botão “próximo” está desativado, não mostrando mais páginas
    is_disabled = await next_button.get_attribute("disabled") is not None
    if is_disabled:
        break  # Pare se não houver mais páginas para navegar

    # Navegue para a próxima página
    await next_button.click()
    await asyncio.sleep(3)  # Aguarde até que a página carregue completamente