"""
Fase 3: Enriquecimento das vagas únicas com descrições e skills.

Lê uma fatia de data/silver/vagas_unicas.csv, visita cada URL individualmente
e preenche o campo 'Skills Necessarias'. Salva em data/silver/enriquecido_INICIO_FIM.csv.

Uso:
  # Primeira execução do perfil (faz login)
  python enriquecer.py --inicio 0 --fim 25000 --perfil chrome-profile-e1

  # Execuções seguintes
  python enriquecer.py --inicio 0 --fim 25000 --perfil chrome-profile-e1 --assume-logged-in

Pré-requisito:
  deduplicar.py deve ter rodado e gerado data/silver/vagas_unicas.csv
"""

import argparse
import asyncio
import platform
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page

BASE_DIR = Path(__file__).resolve().parent
SILVER_DIR = BASE_DIR / "data" / "silver"
INPUT_FILE = SILVER_DIR / "vagas_unicas.csv"

GLASSDOOR_URL = "https://www.glassdoor.com.br/Job/index.htm"

SELETORES_DESC = [
    "[data-test='jobDescriptionText']",
    "[class*='JobDetails_jobDetailsSection']",
    "#JobDescriptionContainer",
    "[class*='jobDescription']",
    "[class*='desc']",
]

TIMEOUT_VAGA = 15_000
MAX_TENTATIVAS = 2
FALHAS_PARA_PAUSA = 5
PAUSA_THROTTLE = 120


async def pausa_humana(media: float = 3.0, desvio: float = 1.2, minimo: float = 0.8) -> None:
    delay = max(minimo, np.random.normal(media, desvio))
    await asyncio.sleep(delay)


async def fechar_popup(page: Page) -> None:
    popups = await page.query_selector_all(".icon-button_IconButton__nMTOc")
    for popup in popups:
        if await popup.is_visible():
            await popup.click()
            await asyncio.sleep(0.5)
            break


async def primeiro_texto(page: Page, seletores: list[str]) -> str:
    for seletor in seletores:
        elementos = await page.query_selector_all(seletor)
        for el in elementos:
            texto = (await el.text_content() or "").strip()
            if texto:
                return texto
    return ""


def _args_antibot() -> list[str]:
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]


async def aguardar_login(page: Page, session_marker: Path, assume_logged_in: bool) -> bool:
    await page.goto(GLASSDOOR_URL)
    await pausa_humana(3.0, 0.8)

    seletores_login = [
        '//button[contains(., "Continuar com o Google")]',
        '//button[contains(., "Entrar")]',
        '[data-test="sign-in-button"]',
    ]

    async def login_exigido() -> bool:
        for seletor in seletores_login:
            try:
                if seletor.startswith("//"):
                    el = await page.query_selector(f"xpath={seletor}")
                else:
                    el = await page.query_selector(seletor)
                if el and await el.is_visible():
                    return True
            except Exception:
                pass
        return False

    if session_marker.exists() and not await login_exigido():
        print("Sessão ativa — iniciando enriquecimento.\n")
        return True

    if session_marker.exists():
        session_marker.unlink(missing_ok=True)

    if assume_logged_in:
        print("ERRO: sessão inativa e --assume-logged-in está ativo.")
        print(f"Rode sem --assume-logged-in para fazer login no perfil '{session_marker.parent.name}'.")
        return False

    print("\n" + "=" * 60)
    print("LOGIN NECESSÁRIO")
    print("=" * 60)
    print("No Chrome que abriu, faça login no Glassdoor:")
    print("  1. Clique em 'Entrar' → 'Continuar com Google'")
    print("  2. Conclua o login e volte aqui")
    print("=" * 60 + "\n")
    input("Pressione Enter quando estiver logado... ")

    session_marker.touch()
    print("Login confirmado.\n")
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enriquecimento de vagas únicas — Fase 3"
    )
    parser.add_argument(
        "--inicio", type=int, default=0,
        help="Índice inicial da fatia em vagas_unicas.csv (default: 0)"
    )
    parser.add_argument(
        "--fim", type=int, default=None,
        help="Índice final da fatia, exclusivo (default: todas)"
    )
    parser.add_argument(
        "--perfil", type=str, default="chrome-profile-enrich",
        help="Pasta do perfil Chrome (default: chrome-profile-enrich)"
    )
    parser.add_argument(
        "--assume-logged-in", action="store_true",
        help="Não pede login interativo; sai se a sessão estiver inativa"
    )
    args = parser.parse_args()

    load_dotenv(BASE_DIR / ".env")

    chrome_profile_dir = BASE_DIR / args.perfil
    session_marker = chrome_profile_dir / ".session"

    if not INPUT_FILE.exists():
        print(f"Arquivo não encontrado: {INPUT_FILE}")
        print("Execute deduplicar.py primeiro.")
        return

    # Lê apenas a fatia necessária — evita carregar o CSV inteiro por terminal
    fim_arg = args.fim
    if fim_arg is None:
        # Precisa saber o total de linhas só para calcular o fim
        fim_arg = sum(1 for _ in open(INPUT_FILE, encoding="utf-8")) - 1  # -1 pelo header
    fim = fim_arg
    fatia = pd.read_csv(
        INPUT_FILE,
        dtype=str,
        skiprows=range(1, args.inicio + 1) if args.inicio > 0 else None,
        nrows=fim - args.inicio,
    ).fillna("")
    fatia = fatia.reset_index(drop=True)

    pendentes_mask = fatia["Skills Necessarias"].isin(["NF", ""]) & fatia["URL"].str.strip().ne("")
    n_pendentes = pendentes_mask.sum()
    n_sem_url = fatia["URL"].str.strip().eq("").sum()

    output_file = SILVER_DIR / f"enriquecido_{args.inicio}_{fim}.csv"

    print(f"Perfil Chrome:  {chrome_profile_dir}")
    print(f"Fatia:          [{args.inicio}:{fim}] → {len(fatia):,} vagas")
    print(f"Pendentes:      {n_pendentes:,}")
    print(f"Sem URL:        {n_sem_url:,} (serão ignoradas)")
    print(f"Saída:          {output_file}\n")

    if output_file.exists():
        print("Arquivo de saída já existe — retomando do ponto onde parou.")
        df_existente = pd.read_csv(output_file, dtype=str).fillna("")
        # Marca como já feitas as que têm descrição no arquivo existente
        ja_enriquecidas = df_existente[df_existente["Skills Necessarias"].ne("NF")].index
        fatia.loc[ja_enriquecidas, "Skills Necessarias"] = df_existente.loc[
            ja_enriquecidas, "Skills Necessarias"
        ]
        pendentes_mask = fatia["Skills Necessarias"].isin(["NF", ""]) & fatia["URL"].str.strip().ne("")
        print(f"Ainda pendentes após retomada: {pendentes_mask.sum():,}\n")

    if n_pendentes == 0:
        print("Nenhuma vaga pendente nesta fatia.")
        return

    chrome_profile_dir.mkdir(parents=True, exist_ok=True)
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        try:
            context: BrowserContext = await p.chromium.launch_persistent_context(
                user_data_dir=str(chrome_profile_dir),
                channel="chrome",
                headless=False,
                args=_args_antibot(),
                ignore_default_args=["--enable-automation"],
                viewport={"width": 1280, "height": 900},
            )
        except Exception as e:
            if "existing browser session" in str(e) or "already in use" in str(e):
                print("\nERRO: o perfil do Chrome ainda está em uso.")
                print(f"Execute: pkill -f '{chrome_profile_dir}'\n")
                return
            raise

        page = context.pages[0] if context.pages else await context.new_page()

        ok = await aguardar_login(page, session_marker, args.assume_logged_in)
        if not ok:
            await context.close()
            return

        falhas_consecutivas = 0
        total_enriquecidas = 0
        indices_pendentes = fatia[pendentes_mask].index.tolist()

        for i, idx in enumerate(indices_pendentes, 1):
            url = fatia.at[idx, "URL"]
            funcao = fatia.at[idx, "Funcao"]

            sucesso = False
            for tentativa in range(MAX_TENTATIVAS):
                try:
                    await page.goto(url, timeout=TIMEOUT_VAGA)
                    await pausa_humana(2.0, 0.6)
                    await fechar_popup(page)

                    desc = await primeiro_texto(page, SELETORES_DESC)
                    fatia.at[idx, "Skills Necessarias"] = desc if desc else "NF"

                    print(f"[{i}/{len(indices_pendentes)}] {funcao[:60]}")
                    falhas_consecutivas = 0
                    total_enriquecidas += 1
                    sucesso = True
                    break
                except Exception:
                    if tentativa < MAX_TENTATIVAS - 1:
                        await asyncio.sleep(3 * (tentativa + 1))

            if not sucesso:
                falhas_consecutivas += 1
                print(f"[{i}/{len(indices_pendentes)}] Falhou — {funcao[:60]}")

                if falhas_consecutivas >= FALHAS_PARA_PAUSA:
                    print(f"  {falhas_consecutivas} falhas seguidas — pausando {PAUSA_THROTTLE}s...")
                    await asyncio.sleep(PAUSA_THROTTLE)
                    falhas_consecutivas = 0

            # Salva progresso a cada 50 vagas para não perder tudo em caso de crash
            if i % 50 == 0:
                fatia.to_csv(output_file, index=False)
                print(f"  [checkpoint] {i}/{len(indices_pendentes)} salvo em {output_file.name}")

            await pausa_humana(1.2, 0.4)

        await context.close()

    fatia.to_csv(output_file, index=False)
    print(f"\nSalvo em: {output_file}")
    print(f"Enriquecidas: {total_enriquecidas:,}")
    print(f"Sem descrição: {pendentes_mask.sum() - total_enriquecidas:,}")
    print(f"\nQuando todos os terminais terminarem, rode: python mesclar.py")


if __name__ == "__main__":
    asyncio.run(main())
