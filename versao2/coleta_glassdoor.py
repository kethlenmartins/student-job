"""
Coleta de vagas no Glassdoor Brasil via Playwright (camada Bronze).

Arquitetura medalhão:
  - Bronze (este script): dados brutos da web, sem filtros de negócio
  - Silver (futuro): limpeza, normalização, deduplicação
  - Gold (futuro): análises e agregações

Busca por UF: para cada estado, testa todas as palavras-chave de
palavras-chave-vagas.txt. Prioridade: SP, RJ, PR, SC, RS, MG, depois demais UFs.
Salva um CSV por combinação em data/bronze/.

Uso:
  python coleta_glassdoor.py

Na primeira execução o Chrome abre e pede login no Glassdoor.
A sessão fica salva em chrome-profile/ para as próximas vezes.
"""

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
CHROME_PROFILE_DIR = BASE_DIR / "chrome-profile"
SESSION_MARKER = CHROME_PROFILE_DIR / ".session"
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"
OUTPUT_DIR = BRONZE_DIR
GLASSDOOR_VAGAS_URL = "https://www.glassdoor.com.br/Job/index.htm"

MAX_VAGAS_POR_BUSCA = 5000  # teto alto para descobrir o limite real do Glassdoor
VAGAS_POR_PAGINA = 30

LOCALIZACOES_PRIORITARIAS = ["SP", "RJ", "PR", "SC", "RS", "MG"]
LOCALIZACOES_RESTANTES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "PA", "PB", "PE", "PI", "RN", "RO", "RR", "SE", "TO", "Brasil",
]

NOMES_ESTADOS = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SE": "Sergipe",
    "SP": "São Paulo",
    "TO": "Tocantins",
    "Brasil": "Brasil",
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
    """Texto completo para o campo de localização, incluindo ', Brasil'."""
    if uf == "Brasil":
        return "Brasil"
    return f"{NOMES_ESTADOS.get(uf, uf)}, Brasil"


def _pontuar_opcao_uf(texto_norm: str, uf: str) -> int:
    """
    Pontua opções do autocomplete para achar o nível estado, não cidade.

    Glassdoor retorna algo como:
      "SP, Brasil"                    → estado   (queremos este, score 100)
      "São Paulo, SP, Brasil"         → cidade   (score 50)
      "São Paulo, São Paulo, Brasil"  → cidade   (score 0)
    """
    if not texto_norm:
        return 0

    if uf == "Brasil":
        return 100 if texto_norm in ("brasil", "brasil, brasil") else 0

    uf_lower = uf.lower()
    nome = normalizar_texto(NOMES_ESTADOS.get(uf, ""))

    # Opção que começa com a sigla: "SP, Brasil"
    if re.match(rf"^{re.escape(uf_lower)},", texto_norm):
        return 100

    # Só o nome do estado + país (sem cidade na frente): "São Paulo, Brasil"
    if texto_norm.startswith(f"{nome},") and texto_norm.count(",") == 1:
        return 90

    # Sigla aparece no meio (cidade, SP, Brasil) — é cidade
    if re.search(rf",\s*{re.escape(uf_lower)}[,\s]", texto_norm):
        return 50

    return 0


def _url_estavel(href: str) -> str:
    """Remove tokens de sessão que expiram (jrtk=) e retém só o jobListingId."""
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
    """Delay com distribuição normal para simular comportamento humano."""
    delay = max(minimo, np.random.normal(media, desvio))
    await asyncio.sleep(delay)


async def pausa_rapida() -> None:
    """Pausa curta entre ações na mesma página."""
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

    async def _limpar_campo(self, seletor: str) -> None:
        campo = await self.page.wait_for_selector(seletor, timeout=10_000)
        await campo.click()
        await pausa_rapida()
        modificador = "Meta" if platform.system() == "Darwin" else "Control"
        await self.page.keyboard.press(f"{modificador}+a")
        await self.page.keyboard.press("Backspace")
        await pausa_rapida()

    async def _digitar_lento(self, texto: str) -> None:
        """Digita com delay variável entre teclas para parecer humano."""
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
        """Coordenadas do centro da coluna esquerda (lista de vagas)."""
        vp = self.page.viewport_size or {"width": 1280, "height": 900}
        return vp["width"] // 4, vp["height"] // 2

    async def _scroll_mouse(self, delta_y: int) -> None:
        """Scroll via evento de roda do mouse na coluna de vagas."""
        x, y = self._pos_coluna_esquerda()
        await self.page.mouse.move(x, y)
        await self.page.mouse.wheel(0, delta_y)

    async def _scroll_suave(self) -> None:
        """Scroll gradual simulando leitura humana da lista de vagas."""
        for _ in range(3):
            await self._scroll_mouse(400)
            await asyncio.sleep(np.random.uniform(0.4, 0.8))

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def _login_exigido(self) -> bool:
        """Retorna True se a página está exigindo autenticação."""
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

    async def aguardar_login(self) -> None:
        await self.page.goto(GLASSDOOR_VAGAS_URL)
        await pausa_humana(media=3.0, desvio=0.8)

        if SESSION_MARKER.exists() and not await self._login_exigido():
            print("Sessão ativa — iniciando coleta.\n")
            return

        # Sessão expirada ou primeira execução
        if SESSION_MARKER.exists():
            SESSION_MARKER.unlink(missing_ok=True)
            print("Sessão expirada — faça login novamente.\n")

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

        SESSION_MARKER.touch()
        print("Login confirmado. Iniciando coleta...\n")

    # ------------------------------------------------------------------
    # Preenchimento de localização
    # ------------------------------------------------------------------

    async def _selecionar_opcao_estado(self, uf: str) -> bool:
        """Escolhe a opção de nível estado no autocomplete (ex: 'SP, Brasil').

        Usa navegação por teclado (ArrowDown + Enter) em vez de mouse click.
        Componentes React de autocomplete geralmente tratam eventos de teclado
        de forma mais confiável — o ArrowDown move o "highlighted" interno do
        componente, que carrega o locId correto antes do Enter confirmar.
        """
        try:
            await self.page.wait_for_selector(self.SELETOR_AUTOCOMPLETE, timeout=5_000)
        except Exception:
            return False

        await asyncio.sleep(0.5)

        opcoes = await self.page.query_selector_all(self.SELETOR_AUTOCOMPLETE)

        # Coleta textos e scores de todas as opções visíveis
        candidatos: list[tuple[int, int, str]] = []  # (score, posição, texto)
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

        # Só aceita opção clara de estado (score ≥ 75); cidades têm score 50
        if melhor_score < 75:
            print(f"    Autocomplete: '{melhor_texto}' score={melhor_score} < 75, ignorando")
            return False

        print(f"    Autocomplete: '{melhor_texto}' (score {melhor_score}, pos {melhor_pos + 1})")

        # Navega até a opção via teclado — mais confiável para React dropdowns
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

        # Tab confirma a seleção e tira o foco do campo (essencial para o form funcionar)
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
        await self.page.keyboard.press("Escape")
        await asyncio.sleep(0.2)

        # Clica o botão de pesquisa via JS (sem hover, sem risco de timeout)
        clicou = await self.page.evaluate("""
            () => {
                const btn = document.querySelector('[data-test="search-bar-submit"]')
                         || document.querySelector('button[type="submit"]')
                         || Array.from(document.querySelectorAll('button')).find(b =>
                               b.textContent.includes('Pesquisar') ||
                               b.textContent.includes('Search') ||
                               (b.getAttribute('aria-label') || '').includes('Pesquisar'));
                if (btn) { btn.click(); return true; }
                return false;
            }
        """)
        if not clicou:
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
        """Navega para a página limpa e preenche a localização (uma vez por UF)."""
        await self.page.goto(GLASSDOOR_VAGAS_URL)
        await pausa_humana(media=2.5, desvio=0.8)
        await self._fechar_popup()
        ok = await self._preencher_localizacao(uf)
        if ok:
            print(f"    UF {uf} ({nome_estado(uf)}) pronta para buscas.")
        return ok

    async def buscar_palavra_chave(self, palavra_chave: str, uf: str) -> bool:
        """Preenche só o cargo e submete (localização já definida por preparar_uf)."""
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

    async def buscar(self, palavra_chave: str, uf: str) -> bool:
        """Busca completa: navega de volta ao início, redefine local + cargo."""
        ok = await self.preparar_uf(uf)
        if not ok:
            print(f"    Aviso: localização '{nome_estado(uf)}' pode não ter sido aplicada.")
        return await self.buscar_palavra_chave(palavra_chave, uf)

    # ------------------------------------------------------------------
    # Extração de cards
    # ------------------------------------------------------------------

    async def _listar_cards(self) -> list:
        return await self.page.query_selector_all(self.SELETOR_CARDS)

    async def _carregar_mais_vagas(self) -> bool:
        """Encontra e clica no botão 'ver mais vagas'."""
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

        # Fallback via JS
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

        # Captura URL diretamente do link no card (sem clicar).
        # Prefere links /Job/ permanentes; partner/jobListing.htm com jrtk= expiram rapidamente.
        for seletor_link in ["a[href*='/Job/'][href*='.htm']", "a[href*='/Job/']", "a[data-test='job-link']", "a[href*='job-listing']", "a"]:
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

    async def coletar_vagas(self, palavra_chave: str, uf: str) -> list[dict]:
        """
        Itera pelos cards sem clicar em cada um individualmente.
        Cliques causam re-renders que resetam o scroll e invalidam ElementHandles.
        A URL de cada vaga é salva no CSV para consulta posterior.
        """
        vagas: list[dict] = []
        vistos: set[str] = set()  # dedup por título+empresa

        rodadas_sem_novos = 0

        while len(vagas) < MAX_VAGAS_POR_BUSCA:
            cards = await self._listar_cards()
            novos_nesta_rodada = 0

            for card in cards:
                try:
                    vaga = await self._extrair_card(card, palavra_chave, uf)
                    chave = f"{vaga['Funcao']}|{vaga['Empresa']}"
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
                    break  # sem progresso após tentar carregar mais
            else:
                rodadas_sem_novos = 0

            if not await self._carregar_mais_vagas():
                break

        if not vagas:
            print(f"    Nenhuma vaga coletada — URL: {self.page.url}")
            return vagas

        url_resultados = self.page.url
        await self._enriquecer_descricoes(vagas)
        # Volta para a página de resultados para que a próxima busca_palavra_chave
        # encontre o formulário correto (com localização já preenchida)
        await self.page.goto(url_resultados)
        await pausa_humana(media=2.0, desvio=0.5)
        return vagas

    async def _enriquecer_descricoes(self, vagas: list[dict]) -> None:
        """
        Fase 2: visita cada URL de vaga individualmente para extrair a descrição.
        Usa timeout reduzido para falhar rápido, retry com backoff e pausa longa
        ao detectar throttling por falhas consecutivas.
        """
        SELETORES_DESC = [
            "[data-test='jobDescriptionText']",
            "[class*='JobDetails_jobDetailsSection']",
            "#JobDescriptionContainer",
            "[class*='jobDescription']",
            "[class*='desc']",
        ]
        TIMEOUT_VAGA = 15_000  # 15s — falha rápido em vez de travar 30s por URL
        MAX_TENTATIVAS = 2
        FALHAS_PARA_PAUSA = 5
        PAUSA_THROTTLE = 120  # segundos

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

                    desc = await self._primeiro_texto(self.page, SELETORES_DESC)
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
                print(f"    [{i}/{len(com_url)}] Falhou após {MAX_TENTATIVAS} tentativas — {vaga['Funcao'][:60]}")

                if falhas_consecutivas >= FALHAS_PARA_PAUSA:
                    print(f"    {falhas_consecutivas} falhas seguidas — pausando {PAUSA_THROTTLE}s para evitar bloqueio...")
                    await asyncio.sleep(PAUSA_THROTTLE)
                    falhas_consecutivas = 0

            await pausa_humana(media=1.2, desvio=0.4)


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------


def _fechar_chrome_com_perfil(profile_dir: Path) -> None:
    """Encerra qualquer instância de Chrome que esteja usando o perfil da coleta."""
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
    load_dotenv(BASE_DIR / ".env")

    palavras_chave = carregar_palavras_chave(KEYWORDS_FILE)
    localizacoes = localizacoes_ordenadas()
    total_buscas = len(palavras_chave) * len(localizacoes)
    ja_feitas = sum(
        1 for uf in localizacoes for pk in palavras_chave if _busca_concluida(pk, uf)
    )
    pendentes = total_buscas - ja_feitas

    print(f"Palavras-chave: {len(palavras_chave)}")
    print(f"Localizações:   {len(localizacoes)} (prioridade: {', '.join(LOCALIZACOES_PRIORITARIAS)})")
    print(f"Total de buscas: {total_buscas}  |  Já feitas: {ja_feitas}  |  Pendentes: {pendentes}")
    print(f"Saída: {OUTPUT_DIR}\n")

    if pendentes == 0:
        print("Todas as buscas já foram concluídas.")
        return

    for pasta in (BRONZE_DIR, SILVER_DIR, GOLD_DIR):
        pasta.mkdir(parents=True, exist_ok=True)
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    _fechar_chrome_com_perfil(CHROME_PROFILE_DIR)

    async with async_playwright() as p:
        try:
            context: BrowserContext = await p.chromium.launch_persistent_context(
                user_data_dir=str(CHROME_PROFILE_DIR),
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
                print(f"Ou execute: pkill -f '{CHROME_PROFILE_DIR}'\n")
                return
            raise
        page = context.pages[0] if context.pages else await context.new_page()

        coletor = ColetorGlassdoor(page)
        await coletor.aguardar_login()

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
                    vagas = await coletor.coletar_vagas(palavra_chave, uf)
                    salvar_csv(vagas, arquivo)
                except Exception as erro:
                    print(f"    Erro na coleta: {erro}")
                    print("    Continuando para a próxima busca...")

        await context.close()
    print("\nColeta finalizada.")


if __name__ == "__main__":
    asyncio.run(main())
