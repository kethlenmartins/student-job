"""Enriquecimento com concorrência limitada e persistência incremental.

Esta versão mantém um único processo Chrome por comando e usa um pequeno pool
de abas. Ao contrário de ``enriquecer.py``, ela não conserva a fatia inteira
na RAM e não regrava um CSV grande a cada checkpoint.

Exemplos:
  python enriquecer_paralelo.py --inicio 0 --fim 5000 --perfil chrome-profile-e1
  python enriquecer_paralelo.py --inicio 0 --fim 5000 --perfil chrome-profile-e1 \
      --assume-logged-in --workers 2

O arquivo de saída é um CSV de resultados, gravado linha a linha, e pode ser
retomado com o mesmo comando. Use perfis e intervalos diferentes entre
máquinas; não compartilhe uma pasta de perfil Chrome entre processos.
"""

import argparse
import asyncio
import csv
import os
import platform
import random
import sys
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright

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
FALHAS_PARA_RECRIAR_ABA = 3


async def pausa(media: float, desvio: float, minimo: float = 0.3) -> None:
    await asyncio.sleep(max(minimo, random.gauss(media, desvio)))


def _args_antibot() -> list[str]:
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]


async def fechar_popup(page: Page) -> None:
    for popup in await page.query_selector_all(".icon-button_IconButton__nMTOc"):
        if await popup.is_visible():
            await popup.click()
            await asyncio.sleep(0.3)
            return


async def primeiro_texto(page: Page) -> str:
    for seletor in SELETORES_DESC:
        for el in await page.query_selector_all(seletor):
            texto = (await el.text_content() or "").strip()
            if texto:
                return texto
    return ""


async def login_exigido(page: Page) -> bool:
    for seletor in (
        'xpath=//button[contains(., "Continuar com o Google")]',
        'xpath=//button[contains(., "Entrar")]',
        '[data-test="sign-in-button"]',
    ):
        try:
            el = await page.query_selector(seletor)
            if el and await el.is_visible():
                return True
        except Exception:
            continue
    return False


async def aguardar_login(page: Page, marker: Path, assume_logged_in: bool) -> bool:
    await page.goto(GLASSDOOR_URL)
    await pausa(3, 0.8)
    if marker.exists() and not await login_exigido(page):
        print("Sessão ativa — iniciando enriquecimento.")
        return True
    marker.unlink(missing_ok=True)
    if assume_logged_in:
        print("ERRO: sessão inativa; rode uma vez sem --assume-logged-in.")
        return False
    print("\nFaça login no Chrome aberto e retorne a este terminal.")
    input("Pressione Enter quando estiver logado... ")
    marker.touch()
    return True


def linhas_concluidas(output_file: Path, retry_errors: bool) -> set[int]:
    """Lê apenas índice e status, sem carregar descrições já gravadas."""
    if not output_file.exists():
        return set()
    concluidas: set[int] = set()
    with output_file.open(encoding="utf-8", newline="") as arquivo:
        for row in csv.DictReader(arquivo):
            if retry_errors and row.get("Status enriquecimento") == "erro":
                continue
            try:
                # queue_index é local à fila filtrada; source_index aponta para
                # a linha original no Silver e é preservado no resultado.
                chave = row.get("queue_index") or row.get("source_index")
                concluidas.add(int(chave))
            except (KeyError, TypeError, ValueError):
                continue
    return concluidas


def total_linhas(caminho: Path) -> int:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        # DictReader respeita quebras de linha dentro de campos CSV citados.
        return sum(1 for _ in csv.DictReader(arquivo))


def reiniciar_processo(motivo: str, limite: int) -> None:
    """Relança o Python sem perder o progresso já persistido no CSV.

    Um contexto Playwright pode ficar conectado a um Chrome que não responde;
    nesse estado criar outra aba no mesmo contexto normalmente não resolve.
    ``execv`` substitui este processo pelo mesmo comando, sem exigir que a
    pessoa acompanhe o terminal. A execução seguinte lê o CSV incremental e
    pula todas as linhas já gravadas.
    """
    nome_variavel = "WEBSCRAPPING_V3_AUTO_RESTARTS"
    try:
        numero = int(os.environ.get(nome_variavel, "0"))
    except ValueError:
        numero = 0
    if numero >= limite:
        raise RuntimeError(
            f"Chrome permaneceu indisponível após {numero} reinícios automáticos. "
            "O progresso foi salvo; verifique rede/login e rode o mesmo comando."
        )
    os.environ[nome_variavel] = str(numero + 1)
    print(
        f"\n[watchdog] {motivo}. Reiniciando Chrome e retomando "
        f"automaticamente ({numero + 1}/{limite})...\n",
        flush=True,
    )
    # As linhas que falharam imediatamente antes da reinicialização podem ter
    # sido gravadas como ``erro``. Na retomada elas precisam voltar para a
    # fila, enquanto as linhas bem-sucedidas continuam sendo puladas.
    argumentos = [sys.executable, *sys.argv]
    if "--retry-errors" not in argumentos:
        argumentos.append("--retry-errors")
    os.execv(sys.executable, argumentos)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Enriquecimento paralelo com baixo uso de RAM")
    parser.add_argument("--inicio", type=int, default=0)
    parser.add_argument("--fim", type=int)
    parser.add_argument(
        "--input-file", type=Path, default=INPUT_FILE,
        help="CSV da fila a enriquecer (default: data/silver/vagas_unicas.csv)",
    )
    parser.add_argument("--perfil", default="chrome-profile-enrich")
    parser.add_argument("--workers", type=int, default=2, help="Abas simultâneas (recomendado: 2; máximo: 4)")
    parser.add_argument("--assume-logged-in", action="store_true")
    parser.add_argument("--retry-errors", action="store_true", help="Tenta de novo apenas linhas que terminaram com erro")
    parser.add_argument(
        "--timeout-item", type=int, default=60,
        help="Segundos máximos para processar uma vaga inteira (default: 60)",
    )
    parser.add_argument(
        "--max-auto-restarts", type=int, default=8,
        help="Máximo de reinícios automáticos do Chrome antes de parar (default: 8)",
    )
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        parser.error("--workers deve estar entre 1 e 4")
    if args.timeout_item < 20:
        parser.error("--timeout-item deve ser pelo menos 20 segundos")
    if args.max_auto_restarts < 0:
        parser.error("--max-auto-restarts não pode ser negativo")
    input_file = args.input_file.resolve()
    if not input_file.exists():
        print(f"Arquivo não encontrado: {input_file}")
        return

    fim = args.fim if args.fim is not None else total_linhas(input_file)
    if args.inicio < 0 or fim <= args.inicio:
        parser.error("o intervalo --inicio/--fim é inválido")
    output_dir = input_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"enriquecido_paralelo_{input_file.stem}_{args.inicio}_{fim}.csv"
    concluidas = linhas_concluidas(output_file, args.retry_errors)
    perfil = BASE_DIR / args.perfil
    print(f"Entrada: {input_file}")
    print(f"Fatia: [{args.inicio}:{fim}] | abas: {args.workers} | já persistidas: {len(concluidas):,}")
    print(f"Saída incremental: {output_file.name}")

    # Cada item ocupa uma linha e a fila é limitada: não há acúmulo de vagas
    # nem descrições em memória quando a entrada possui dezenas de milhares de linhas.
    fila: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=args.workers * 2)
    escrita = asyncio.Lock()
    contador = {"ok": 0, "erro": 0, "feito": 0}

    with input_file.open(encoding="utf-8", newline="") as entrada:
        reader = csv.DictReader(entrada)
        campos = list(reader.fieldnames or [])
    obrigatorios = {"URL", "Skills Necessarias", "Funcao"}
    ausentes = obrigatorios - set(campos)
    if ausentes:
        parser.error(f"colunas ausentes em vagas_unicas.csv: {', '.join(sorted(ausentes))}")
    if "source_index" not in campos:
        campos.append("source_index")
    output_campos = ["queue_index", *campos, "Status enriquecimento"]
    novo_arquivo = not output_file.exists() or output_file.stat().st_size == 0
    arquivo_saida = output_file.open("a", encoding="utf-8", newline="")
    writer = csv.DictWriter(arquivo_saida, fieldnames=output_campos, extrasaction="ignore")
    if novo_arquivo:
        writer.writeheader()
        arquivo_saida.flush()

    async def gravar(row: dict, indice: int, status: str) -> None:
        row = dict(row)
        row.setdefault("source_index", indice)
        row["queue_index"] = indice
        row["Status enriquecimento"] = status
        async with escrita:
            writer.writerow(row)
            arquivo_saida.flush()

    async def worker(numero: int, page: Page) -> None:
        falhas_na_aba = 0
        recriacoes_da_aba = 0

        async def buscar_descricao(row: dict, url: str) -> str:
            """Limite externo protege também chamadas Playwright que ignoram timeout."""
            for tentativa in range(MAX_TENTATIVAS):
                try:
                    await page.goto(url, timeout=TIMEOUT_VAGA, wait_until="domcontentloaded")
                    await pausa(1.4, 0.4)
                    await fechar_popup(page)
                    return await primeiro_texto(page)
                except Exception:
                    if tentativa + 1 < MAX_TENTATIVAS:
                        await asyncio.sleep(2 * (tentativa + 1))
            raise RuntimeError("não foi possível obter a página após as tentativas")

        while True:
            item = await fila.get()
            if item is None:
                fila.task_done()
                return
            indice, row = item["indice"], item["row"]
            url = row.get("URL", "").strip()
            status = "erro"
            if not url:
                status = "sem_url"
            elif row.get("Skills Necessarias", "").strip() not in {"", "NF"}:
                status = "ja_preenchida"
            else:
                try:
                    descricao = await asyncio.wait_for(
                        buscar_descricao(row, url), timeout=args.timeout_item
                    )
                    row["Skills Necessarias"] = descricao or "NF"
                    status = "ok" if descricao else "sem_descricao"
                    falhas_na_aba = 0
                    recriacoes_da_aba = 0
                except TimeoutError:
                    row["Skills Necessarias"] = "NF"
                    print(f"[aba {numero}] timeout total na linha {indice}")
                except Exception as exc:
                    row["Skills Necessarias"] = "NF"
                    print(f"[aba {numero}] erro na linha {indice}: {type(exc).__name__}")

                if status == "erro":
                    falhas_na_aba += 1
                    if falhas_na_aba >= FALHAS_PARA_RECRIAR_ABA:
                        print(f"[watchdog] recriando aba {numero} após {falhas_na_aba} falhas...")
                        try:
                            await asyncio.wait_for(page.close(), timeout=5)
                            page = await asyncio.wait_for(context.new_page(), timeout=15)
                        except Exception as exc:
                            arquivo_saida.flush()
                            reiniciar_processo(
                                f"não foi possível recriar a aba {numero} ({type(exc).__name__})",
                                args.max_auto_restarts,
                            )
                        falhas_na_aba = 0
                        recriacoes_da_aba += 1
                        if recriacoes_da_aba >= 3:
                            arquivo_saida.flush()
                            reiniciar_processo(
                                f"a aba {numero} travou repetidamente",
                                args.max_auto_restarts,
                            )
            await gravar(row, indice, status)
            contador["feito"] += 1
            contador["ok" if status == "ok" else "erro"] += 1
            if contador["feito"] % 25 == 0:
                print(f"  {contador['feito']:,} resultados persistidos | descrições: {contador['ok']:,}")
            fila.task_done()
            await pausa(0.8, 0.25)

    async with async_playwright() as p:
        perfil.mkdir(parents=True, exist_ok=True)
        try:
            context: BrowserContext = await p.chromium.launch_persistent_context(
                user_data_dir=str(perfil), channel="chrome", headless=False,
                args=_args_antibot(), ignore_default_args=["--enable-automation"],
                viewport={"width": 1280, "height": 900},
            )
        except Exception as exc:
            arquivo_saida.close()
            print(f"Não foi possível abrir o perfil Chrome: {exc}")
            return
        paginas = list(context.pages)
        pagina_login = paginas[0] if paginas else await context.new_page()
        if not await aguardar_login(pagina_login, perfil / ".session", args.assume_logged_in):
            await context.close()
            arquivo_saida.close()
            return
        while len(paginas) < args.workers:
            paginas.append(await context.new_page())
        tarefas = [asyncio.create_task(worker(n + 1, pagina)) for n, pagina in enumerate(paginas[:args.workers])]

        with input_file.open(encoding="utf-8", newline="") as entrada:
            for indice, row in enumerate(csv.DictReader(entrada)):
                if indice < args.inicio or indice >= fim or indice in concluidas:
                    continue
                await fila.put({"indice": indice, "row": row})
        for _ in tarefas:
            await fila.put(None)
        await fila.join()
        await asyncio.gather(*tarefas)
        await context.close()
    arquivo_saida.close()
    print(f"\nConcluído nesta execução: {contador['feito']:,}; descrições: {contador['ok']:,}; outros: {contador['erro']:,}")
    print(f"Resultado: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
