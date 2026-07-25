"""
Coleta de vagas no Glassdoor Brasil via Playwright — Fase 1 (Bronze).

Arquitetura medalhão:
  - Bronze (este script): cards sem descrição, sem enriquecimento individual
  - Silver (deduplicar.py + enriquecer.py): dedup e descrições
  - Gold (futuro): análises e agregações

Uso:
  # Primeira execução de um perfil (faz login manual)
  python coleta_glassdoor.py --kw-inicio 0 --kw-fim 50 --perfil chrome-profile-t1 --sem-enriquecer

  # Execuções seguintes (sessão já salva)
  python coleta_glassdoor.py --kw-inicio 0 --kw-fim 50 --perfil chrome-profile-t1 --sem-enriquecer --assume-logged-in
"""

import argparse
import ast
import asyncio
import platform
import re
import subprocess
import time
import unicodedata
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
KEYWORDS_FILE = BASE_DIR / "palavras-chave-vagas.txt"
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"
OUTPUT_DIR = BRONZE_DIR
GLASSDOOR_VAGAS_URL = "https://www.glassdoor.com.br/Job/index.htm"

MAX_VAGAS_POR_BUSCA = 5000
VAGAS_POR_PAGINA = 30

LOCALIZACOES_PRIORITARIAS = ["SP", "RJ", "PR", "SC", "RS", "MG"]
LOCALIZACOES_RESTANTES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "PA", "PB", "PE", "PI", "RN", "RO", "RR", "SE", "TO",
]

NOMES_ESTADOS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia",
    "RR": "Roraima", "SC": "Santa Catarina", "SE": "Sergipe",
    "SP": "São Paulo", "TO": "Tocantins",
}


def localizacoes_ordenadas() -> list[str]:
    ordenadas: list[str] = []
    vistos: set[str] = set()
    for uf in LOCALIZACOES_PRIORITARIAS + LOCALIZACOES_RESTANTES:
        if uf not in vistos:
            ordenadas.append(uf)
            vistos.add(uf)
    return ordenadas


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def carregar_palavras_chave(caminho: Path) -> list[str]:
    conteudo = caminho.read_text(encoding="utf-8").strip()
    palavras = ast.literal_eval(conteudo)
    return [p.strip() for p in palavras if p.strip()]


def sanitizar_nome_arquivo(texto: str) -> str:
    nome = re.sub(r"[^\w\-]", "_", texto.strip().lower())
    return re.sub(r"_+", "_", nome).strip("_")[:80]


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def nome_estado(uf: str) -> str:
    return NOMES_ESTADOS.get(uf, uf)


def _local_para_busca(uf: str) -> str:
    return f"{NOMES_ESTADOS.get(uf, uf)}, Brasil"


def _pontuar_opcao_uf(texto_norm: str, uf: str) -> int:
    if not texto_norm:
        return 0
    uf_lower = uf.lower()
    nome = normalizar_texto(NOMES_ESTADOS.get(uf, ""))
    if re.match(rf"^{re.escape(uf_lower)},", texto_norm):
        return 100
    if texto_norm.startswith(f"{nome},") and texto_norm.count(",") == 1:
        return 90
    if re.search(rf",\s*{re.escape(uf_lower)}[,\s]", texto_norm):
        return 50
    return 0


def _url_estavel(href: str) -> str:
    if "jobListingId=" in href:
        m = re.search(r"jobListingId=(\d+)", href)
        if m:
            return f"https://www.glassdoor.com.br/partner/jobListing.htm?jobListingId={m.group(1)}"
    return href


def salvar_csv(vagas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(vagas).to_csv(caminho, index=False)
    print(f"  → {len(vagas)} vagas salvas em {caminho.name}")


async def pausa_humana(media: float = 3.0, desvio: float = 1.2, minimo: float = 0.8) -> None:
    delay = max(minimo, np.random.normal(media, desvio))
    await asyncio.sleep(delay)


async def pausa_rapida() -> None:
    await pausa_humana(media=1.0, desvio=0.35, minimo=0.4)


# ---------------------------------------------------------------------------
# Coletor
# ---------------------------------------------------------------------------


class ColetorGlassdoor:
    SELETOR_CAMPO_CARGO = "#searchBar-jobTitle"
    SELETOR_CAMPO_LOCAL = "#searchBar-location"
    SELETOR_CARDS = "#left-column li[data-test='jobListing']"
    SELETOR_BOTAO_MAIS = "#left-column > div:nth-child(2) > div > button"
    XPATH_BOTAO_MAIS = '//*[@id="left-column"]/div[2]/div/button'
    SELETOR_POPUP = ".icon-button_IconButton__nMTOc"
    SELETOR_AUTOCOMPLETE = "[role='listbox'] [role='option'], [role='listbox'] li"

    SELETORES_TITULO = [
        "[data-test='job-title']",
        "a[class*='JobCard_jobTitle']",
        "[data-test='job-link']",
    ]
    SELETORES_EMPRESA = [
        "[class*='compactEmployerName']",
        "[data-test='employer-name']",
        "[class*='EmployerInfo']",
        "[class*='employerName']",
    ]
    SELETORES_LOCAL_CARD = [
        "[data-test='emp-location']",
        "[data-test='job-location']",
        "[class*='location']",
    ]
    SELETORES_SALARIO = [
        "[data-test='detailSalary']",
        "[class*='Salary']",
        "[class*='salary']",
    ]
    SELETORES_DATA = [
        "[data-test='job-age']",
        "[class*='jobAge']",
        "[class*='listing-age']",
    ]
    SELETORES_DESC = [
        "[data-test='jobDescriptionText']",
        "[class*='JobDetails_jobDetailsSection']",
        "#JobDescriptionContainer",
        "[class*='jobDescription']",
        "[class*='desc']",
    ]

    def __init__(self, page: Page):
        self.page = page

    # ------------------------------------------------------------------
    # Helpers de interação
    # ------------------------------------------------------------------

    async def _fechar_popup(self) -> None:
        popups = await self.page.query_selector_all(self.SELETOR_POPUP)
        for popup in popups:
            if await popup.is_visible():
                await popup.click()
                await pausa_rapida()
                break
        # <dialog open> bloqueia cliques; fecha via Escape, mas só se o dialog
        # não contém o campo de busca (evita fechar a barra de pesquisa do Glassdoor)
        dialog = await self.page.query_selector("dialog[open]")
        if dialog:
            campo_dentro = await dialog.query_selector(self.SELETOR_CAMPO_CARGO)
            if not campo_dentro:
                await self.page.keyboard.press("Escape")
                await pausa_rapida()

    async def _limpar_campo(self, seletor: str) -> None:
        campo = await self.page.wait_for_selector(seletor, timeout=10_000)
        await campo.click()
        await pausa_rapida()
        modificador = "Meta" if platform.system() == "Darwin" else "Control"
        await self.page.keyboard.press(f"{modificador}+a")
        await self.page.keyboard.press("Backspace")
        await pausa_rapida()

    async def _digitar_lento(self, texto: str) -> None:
        for char in texto:
            await self.page.keyboard.type(char)
            await asyncio.sleep(np.random.uniform(0.04, 0.14))

    async def _primeiro_texto(self, raiz, seletores: list[str]) -> str:
        for seletor in seletores:
            elementos = await raiz.query_selector_all(seletor)
            for el in elementos:
                texto = (await el.text_content() or "").strip()
                if texto:
                    return texto
        return ""

    def _pos_coluna_esquerda(self) -> tuple[int, int]:
        vp = self.page.viewport_size or {"width": 1280, "height": 900}
        return vp["width"] // 4, vp["height"] // 2

    async def _scroll_mouse(self, delta_y: int) -> None:
        x, y = self._pos_coluna_esquerda()
        await self.page.mouse.move(x, y)
        await self.page.mouse.wheel(0, delta_y)

    async def _scroll_suave(self) -> None:
        for _ in range(3):
            await self._scroll_mouse(400)
            await asyncio.sleep(np.random.uniform(0.4, 0.8))

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def _login_exigido(self) -> bool:
        seletores_login = [
            '//button[contains(., "Continuar com o Google")]',
            '//button[contains(., "Continue with Google")]',
            '//button[contains(., "Entrar com Google")]',
            '//button[contains(., "Sign in with Google")]',
            '//button[contains(., "Entrar")]',
            '//a[contains(., "Sign In")]',
            '[data-test="sign-in-button"]',
        ]
        for seletor in seletores_login:
            try:
                if seletor.startswith("//"):
                    el = await self.page.query_selector(f"xpath={seletor}")
                else:
                    el = await self.page.query_selector(seletor)
                if el and await el.is_visible():
                    return True
            except Exception:
                pass
        return False

    async def aguardar_login(self, session_marker: Path, assume_logged_in: bool = False) -> None:
        await self.page.goto(GLASSDOOR_VAGAS_URL)
        await pausa_humana(media=3.0, desvio=0.8)

        if session_marker.exists() and not await self._login_exigido():
            print("Sessão ativa — iniciando coleta.\n")
            return

        if session_marker.exists():
            session_marker.unlink(missing_ok=True)
            print("Sessão expirada — faça login novamente.\n")

        if assume_logged_in:
            raise SystemExit(
                "Sessão inativa e --assume-logged-in está ativo.\n"
                f"Rode sem --assume-logged-in para fazer login no perfil '{session_marker.parent.name}'."
            )

        print("\n" + "=" * 60)
        print("LOGIN NECESSÁRIO")
        print("=" * 60)
        print("No Chrome que abriu, faça login no Glassdoor:")
        print("  1. Clique em 'Entrar' → 'Continuar com Google'")
        print("  2. Conclua o login e volte aqui")
        print("  (A sessão ficará salva para as próximas vezes)")
        print("=" * 60 + "\n")
        input("Pressione Enter quando estiver logado... ")

        await self.page.goto(GLASSDOOR_VAGAS_URL)
        await pausa_humana(media=4.0, desvio=1.0)

        try:
            await self.page.wait_for_selector(self.SELETOR_CAMPO_CARGO, timeout=30_000)
        except Exception:
            print("Aviso: campo de busca não encontrado. Verifique se está logado.\n")
            return

        session_marker.touch()
        print("Login confirmado. Iniciando coleta...\n")

    # ------------------------------------------------------------------
    # Preenchimento de localização
    # ------------------------------------------------------------------

    async def _selecionar_opcao_estado(self, uf: str) -> bool:
        try:
            await self.page.wait_for_selector(self.SELETOR_AUTOCOMPLETE, timeout=5_000)
        except Exception:
            return False

        await asyncio.sleep(0.5)
        opcoes = await self.page.query_selector_all(self.SELETOR_AUTOCOMPLETE)

        candidatos: list[tuple[int, int, str]] = []
        pos = 0
        for opcao in opcoes:
            if not await opcao.is_visible():
                continue
            texto = (await opcao.text_content() or "").strip()
            score = _pontuar_opcao_uf(normalizar_texto(texto), uf)
            candidatos.append((score, pos, texto))
            pos += 1

        if not candidatos:
            return False

        melhor_score, melhor_pos, melhor_texto = max(candidatos, key=lambda x: x[0])

        if melhor_score < 75:
            print(f"    Autocomplete: '{melhor_texto}' score={melhor_score} < 75, ignorando")
            return False

        print(f"    Autocomplete: '{melhor_texto}' (score {melhor_score}, pos {melhor_pos + 1})")

        for _ in range(melhor_pos + 1):
            await self.page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.12)

        await self.page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        return True

    async def _preencher_localizacao(self, uf: str) -> bool:
        selecionou = False
        for texto_busca in [nome_estado(uf)]:
            await self._limpar_campo(self.SELETOR_CAMPO_LOCAL)
            await self.page.click(self.SELETOR_CAMPO_LOCAL)
            await self._digitar_lento(texto_busca)
            await pausa_humana(media=1.5, desvio=0.4, minimo=0.8)

            selecionou = await self._selecionar_opcao_estado(uf)
            if selecionou:
                break

        if not selecionou:
            await self.page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.3)
            await self.page.keyboard.press("Enter")
            await pausa_rapida()
            print(f"    Local: nenhum autocomplete, usou seta+Enter")

        await self.page.keyboard.press("Tab")
        await asyncio.sleep(0.5)

        valor = await self.page.input_value(self.SELETOR_CAMPO_LOCAL)
        print(f"    Local no formulário: '{valor}'")
        await self._fechar_popup()
        return bool(valor.strip())

    # ------------------------------------------------------------------
    # Busca
    # ------------------------------------------------------------------

    async def _preencher_cargo(self, palavra_chave: str) -> None:
        await self._limpar_campo(self.SELETOR_CAMPO_CARGO)
        await self.page.click(self.SELETOR_CAMPO_CARGO)
        await self._digitar_lento(palavra_chave)
        await pausa_rapida()

    async def _submeter_busca(self) -> None:
        # Enter no campo é a forma mais confiável: fecha o autocomplete e
        # submete em um passo, sem risco de reverter o valor digitado (Escape)
        await self.page.focus(self.SELETOR_CAMPO_CARGO)
        await asyncio.sleep(0.15)
        await self.page.keyboard.press("Enter")
        await pausa_humana(media=4.0, desvio=1.0)

    async def _aguardar_resultados(self, timeout: float = 20.0) -> bool:
        try:
            await self.page.wait_for_selector(
                self.SELETOR_CARDS, timeout=int(timeout * 1000)
            )
            return True
        except Exception:
            pass

        fonte = (await self.page.content()).lower()
        return not any(
            t in fonte
            for t in ["nenhuma vaga", "no jobs found", "0 vagas", "não encontramos"]
        )

    async def preparar_uf(self, uf: str) -> bool:
        await self.page.goto(GLASSDOOR_VAGAS_URL)
        await pausa_humana(media=2.5, desvio=0.8)
        await self._fechar_popup()
        ok = await self._preencher_localizacao(uf)
        if ok:
            print(f"    UF {uf} ({nome_estado(uf)}) pronta para buscas.")
        return ok

    async def buscar_palavra_chave(self, palavra_chave: str, uf: str) -> bool:
        await self._fechar_popup()
        await self._preencher_cargo(palavra_chave)

        # Na página de resultados, interagir com o campo de cargo pode limpar o
        # campo de localização. Verifica e repreenche antes de submeter.
        try:
            valor_local = await self.page.input_value(self.SELETOR_CAMPO_LOCAL)
        except Exception:
            valor_local = ""
        if not valor_local.strip():
            print(f"    Campo de local vazio — repreenchendo UF {uf}...")
            await self._preencher_localizacao(uf)
            await self._preencher_cargo(palavra_chave)

        await self._submeter_busca()
        await self._fechar_popup()

        if await self._aguardar_resultados():
            print(f"    URL: {self.page.url}")
            return True

        print("    Formulário sem cards — tentando busca por URL...")
        params = urllib.parse.urlencode({
            "sc.keyword": palavra_chave,
            "locKeyword": _local_para_busca(uf),
            "clickSource": "searchBtn",
        })
        await self.page.goto(f"{GLASSDOOR_VAGAS_URL}?{params}")
        await pausa_humana(media=4.0, desvio=1.0)
        await self._fechar_popup()
        encontrou = await self._aguardar_resultados()
        print(f"    URL: {self.page.url}")
        return encontrou

    # ------------------------------------------------------------------
    # Extração de cards
    # ------------------------------------------------------------------

    async def _listar_cards(self) -> list:
        return await self.page.query_selector_all(self.SELETOR_CARDS)

    async def _carregar_mais_vagas(self) -> bool:
        seletores = [
            f"xpath={self.XPATH_BOTAO_MAIS}",
            "xpath=//button[contains(., 'Mostrar mais vagas')]",
            "xpath=//button[contains(., 'Ver mais vagas')]",
            "xpath=//button[contains(., 'Show more jobs')]",
            self.SELETOR_BOTAO_MAIS,
        ]
        for seletor in seletores:
            try:
                botao = await self.page.query_selector(seletor)
                if not botao:
                    continue
                await self.page.evaluate(
                    "el => el.scrollIntoView({block: 'center', behavior: 'instant'})",
                    botao,
                )
                await asyncio.sleep(0.5)
                await botao.click()
                await pausa_humana(media=5.0, desvio=1.5)
                await self._fechar_popup()
                return True
            except Exception:
                continue

        clicou = await self.page.evaluate("""
            () => {
                const termos = ['mais vagas', 'more jobs', 'mostrar mais', 'show more'];
                const botao = Array.from(document.querySelectorAll('button')).find(b =>
                    termos.some(t => b.textContent.toLowerCase().includes(t))
                );
                if (!botao) return false;
                botao.scrollIntoView({block: 'center', behavior: 'instant'});
                botao.click();
                return true;
            }
        """)
        if clicou:
            await pausa_humana(media=5.0, desvio=1.5)
            await self._fechar_popup()
            return True

        return False

    async def _extrair_card(self, card, palavra_chave: str, uf: str) -> dict:
        vaga = {
            "Palavra-chave": palavra_chave,
            "UF buscada": uf,
            "Local buscado": nome_estado(uf),
            "Funcao": "",
            "Localização": "",
            "Empresa": "",
            "Data de Publicacao": "",
            "Skills Necessarias": "NF",
            "Média Salarial": "NF",
            "URL": "",
        }
        vaga["Funcao"] = await self._primeiro_texto(card, self.SELETORES_TITULO)
        vaga["Empresa"] = await self._primeiro_texto(card, self.SELETORES_EMPRESA)
        vaga["Localização"] = await self._primeiro_texto(card, self.SELETORES_LOCAL_CARD)
        vaga["Média Salarial"] = await self._primeiro_texto(card, self.SELETORES_SALARIO) or "NF"
        vaga["Data de Publicacao"] = await self._primeiro_texto(card, self.SELETORES_DATA)

        for seletor_link in [
            "a[href*='/Job/'][href*='.htm']",
            "a[href*='/Job/']",
            "a[data-test='job-link']",
            "a[href*='job-listing']",
            "a",
        ]:
            link = await card.query_selector(seletor_link)
            if link:
                href = await link.get_attribute("href") or ""
                if href:
                    if href.startswith("/"):
                        href = f"https://www.glassdoor.com.br{href}"
                    vaga["URL"] = _url_estavel(href)
                    break

        if not vaga["Funcao"]:
            texto = (await card.text_content() or "").strip()
            linhas = [l.strip() for l in texto.split("\n") if l.strip()]
            if len(linhas) >= 2:
                vaga["Empresa"] = vaga["Empresa"] or linhas[0]
                vaga["Funcao"] = linhas[1]
            if len(linhas) >= 3 and not vaga["Localização"]:
                vaga["Localização"] = linhas[2]

        return vaga

    def _chave_dedup(self, vaga: dict) -> str:
        """Chave de deduplicação dentro de uma busca: jobListingId > hash normalizado."""
        m = re.search(r"jobListingId=(\d+)", vaga.get("URL", ""))
        if m:
            return f"gd:{m.group(1)}"
        funcao = normalizar_texto(vaga["Funcao"])
        empresa = normalizar_texto(vaga["Empresa"])
        local = normalizar_texto(vaga["Localização"])
        return f"txt:{funcao}|{empresa}|{local}"

    async def coletar_vagas(
        self, palavra_chave: str, uf: str, sem_enriquecer: bool = False
    ) -> list[dict]:
        """
        Itera pelos cards sem clicar em cada um.
        Com sem_enriquecer=True, salva apenas o que é visível nos cards
        (Skills Necessarias fica como 'NF' para enriquecer.py preencher depois).
        """
        vagas: list[dict] = []
        vistos: set[str] = set()
        rodadas_sem_novos = 0

        while len(vagas) < MAX_VAGAS_POR_BUSCA:
            cards = await self._listar_cards()
            novos_nesta_rodada = 0

            for card in cards:
                try:
                    vaga = await self._extrair_card(card, palavra_chave, uf)
                    chave = self._chave_dedup(vaga)
                    if chave in vistos or (not vaga["Funcao"] and not vaga["Empresa"]):
                        continue
                    vistos.add(chave)
                    vagas.append(vaga)
                    novos_nesta_rodada += 1
                    if len(vagas) >= MAX_VAGAS_POR_BUSCA:
                        break
                except Exception as e:
                    print(f"    Card: erro na extração — {e}")

            print(f"    {len(vagas)} vagas coletadas até agora ({novos_nesta_rodada} novas)")

            if len(vagas) >= MAX_VAGAS_POR_BUSCA:
                break

            if novos_nesta_rodada == 0:
                rodadas_sem_novos += 1
                if rodadas_sem_novos >= 2:
                    break
            else:
                rodadas_sem_novos = 0

            if not await self._carregar_mais_vagas():
                break

        if not vagas:
            print(f"    Nenhuma vaga coletada — URL: {self.page.url}")
            return vagas

        if not sem_enriquecer:
            url_resultados = self.page.url
            await self._enriquecer_descricoes(vagas)
            await self.page.goto(url_resultados)
            await pausa_humana(media=2.0, desvio=0.5)

        return vagas

    async def _enriquecer_descricoes(self, vagas: list[dict]) -> None:
        TIMEOUT_VAGA = 15_000
        MAX_TENTATIVAS = 2
        FALHAS_PARA_PAUSA = 5
        PAUSA_THROTTLE = 120

        com_url = [v for v in vagas if v.get("URL")]
        print(f"    Buscando descrições para {len(com_url)} vagas...")

        falhas_consecutivas = 0

        for i, vaga in enumerate(com_url, 1):
            sucesso = False
            for tentativa in range(MAX_TENTATIVAS):
                try:
                    await self.page.goto(vaga["URL"], timeout=TIMEOUT_VAGA)
                    await pausa_humana(media=2.0, desvio=0.6)
                    await self._fechar_popup()

                    desc = await self._primeiro_texto(self.page, self.SELETORES_DESC)
                    if desc:
                        vaga["Skills Necessarias"] = desc

                    print(f"    [{i}/{len(com_url)}] {vaga['Funcao']}")
                    falhas_consecutivas = 0
                    sucesso = True
                    break
                except Exception:
                    if tentativa < MAX_TENTATIVAS - 1:
                        await asyncio.sleep(3 * (tentativa + 1))

            if not sucesso:
                falhas_consecutivas += 1
                print(f"    [{i}/{len(com_url)}] Falhou — {vaga['Funcao'][:60]}")

                if falhas_consecutivas >= FALHAS_PARA_PAUSA:
                    print(f"    {falhas_consecutivas} falhas seguidas — pausando {PAUSA_THROTTLE}s...")
                    await asyncio.sleep(PAUSA_THROTTLE)
                    falhas_consecutivas = 0

            await pausa_humana(media=1.2, desvio=0.4)


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------


def _fechar_chrome_com_perfil(profile_dir: Path) -> None:
    if platform.system() not in ("Darwin", "Linux"):
        return
    try:
        resultado = subprocess.run(
            ["pgrep", "-f", str(profile_dir)],
            capture_output=True, text=True,
        )
        if resultado.stdout.strip():
            print("Fechando Chrome anterior com este perfil...")
            subprocess.run(["pkill", "-f", str(profile_dir)], check=False)
            time.sleep(2)
            print("Chrome fechado.\n")
    except Exception:
        pass


def _args_antibot() -> list[str]:
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]


def _arquivo_busca(palavra_chave: str, uf: str) -> Path:
    return OUTPUT_DIR / f"{sanitizar_nome_arquivo(palavra_chave)}_{uf}.csv"


def _busca_concluida(palavra_chave: str, uf: str) -> bool:
    return _arquivo_busca(palavra_chave, uf).exists()


def _uf_completa(palavras_chave: list[str], uf: str) -> bool:
    return all(_busca_concluida(pk, uf) for pk in palavras_chave)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coleta de vagas no Glassdoor — Fase 1 (Bronze)"
    )
    parser.add_argument(
        "--kw-inicio", type=int, default=0,
        help="Índice inicial das keywords (default: 0)"
    )
    parser.add_argument(
        "--kw-fim", type=int, default=None,
        help="Índice final das keywords, exclusivo (default: todas)"
    )
    parser.add_argument(
        "--ufs", type=str, default=None,
        help="UFs a processar, separadas por vírgula (ex: SP,RJ). Default: todas"
    )
    parser.add_argument(
        "--perfil", type=str, default="chrome-profile",
        help="Pasta do perfil Chrome (default: chrome-profile)"
    )
    parser.add_argument(
        "--assume-logged-in", action="store_true",
        help="Não pede login interativo; sai se a sessão estiver inativa"
    )
    parser.add_argument(
        "--sem-enriquecer", action="store_true",
        help="Pula o enriquecimento de descrições (recomendado na Fase 1)"
    )
    args = parser.parse_args()

    load_dotenv(BASE_DIR / ".env")

    chrome_profile_dir = BASE_DIR / args.perfil
    session_marker = chrome_profile_dir / ".session"

    todas_palavras = carregar_palavras_chave(KEYWORDS_FILE)
    palavras_chave = todas_palavras[args.kw_inicio:args.kw_fim]

    todas_localizacoes = localizacoes_ordenadas()
    if args.ufs:
        filtro = [u.strip().upper() for u in args.ufs.split(",")]
        localizacoes = [uf for uf in todas_localizacoes if uf in filtro]
        invalidas = [u for u in filtro if u not in todas_localizacoes]
        if invalidas:
            print(f"Aviso: UFs desconhecidas ignoradas: {invalidas}")
    else:
        localizacoes = todas_localizacoes

    total_buscas = len(palavras_chave) * len(localizacoes)
    ja_feitas = sum(
        1 for uf in localizacoes for pk in palavras_chave if _busca_concluida(pk, uf)
    )
    pendentes = total_buscas - ja_feitas

    print(f"Perfil Chrome:   {chrome_profile_dir}")
    print(f"Keywords:        [{args.kw_inicio}:{args.kw_fim}] → {len(palavras_chave)} palavras")
    print(f"UFs:             {len(localizacoes)}")
    print(f"Total de buscas: {total_buscas}  |  Já feitas: {ja_feitas}  |  Pendentes: {pendentes}")
    print(f"Enriquecimento:  {'desativado (--sem-enriquecer)' if args.sem_enriquecer else 'ativado'}")
    print(f"Saída:           {OUTPUT_DIR}\n")

    if pendentes == 0:
        print("Todas as buscas desta fatia já foram concluídas.")
        return

    for pasta in (BRONZE_DIR, SILVER_DIR, GOLD_DIR):
        pasta.mkdir(parents=True, exist_ok=True)
    chrome_profile_dir.mkdir(parents=True, exist_ok=True)

    _fechar_chrome_com_perfil(chrome_profile_dir)

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
                print("Feche todas as janelas do Chrome manualmente e rode novamente.")
                print(f"Ou execute: pkill -f '{chrome_profile_dir}'\n")
                return
            raise

        page = context.pages[0] if context.pages else await context.new_page()
        coletor = ColetorGlassdoor(page)
        await coletor.aguardar_login(session_marker, args.assume_logged_in)

        busca_atual = 0
        for uf in localizacoes:
            if _uf_completa(palavras_chave, uf):
                busca_atual += len(palavras_chave)
                print(f"\n[{uf}] Todas as {len(palavras_chave)} buscas já concluídas — pulando.")
                continue

            print(f"\n{'=' * 60}")
            print(f"UF: {uf} — {nome_estado(uf)}")
            print(f"{'=' * 60}")

            await coletor.preparar_uf(uf)

            for palavra_chave in palavras_chave:
                busca_atual += 1
                arquivo = _arquivo_busca(palavra_chave, uf)

                if arquivo.exists():
                    print(f"[{busca_atual}/{total_buscas}] {uf} → '{palavra_chave}' — já feita, pulando.")
                    continue

                print(f"[{busca_atual}/{total_buscas}] {uf} → '{palavra_chave}'")

                encontrou = await coletor.buscar_palavra_chave(palavra_chave, uf)
                if not encontrou:
                    print("    Nenhum resultado para esta busca.")

                try:
                    vagas = await coletor.coletar_vagas(
                        palavra_chave, uf, sem_enriquecer=args.sem_enriquecer
                    )
                    salvar_csv(vagas, arquivo)
                except Exception as erro:
                    print(f"    Erro na coleta: {erro}")
                    print("    Continuando para a próxima busca...")

        await context.close()
    print("\nColeta finalizada.")


if __name__ == "__main__":
    asyncio.run(main())
