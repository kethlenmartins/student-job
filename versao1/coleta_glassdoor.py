"""
Coleta de vagas no Glassdoor Brasil via Selenium (camada Bronze).

Arquitetura medalhão:
  - Bronze (este script): dados brutos da web, sem filtros de negócio
  - Silver (futuro): limpeza, normalização, deduplicação
  - Gold (futuro): análises e agregações

Busca por UF: para cada estado, testa todas as palavras-chave de
palavras-chave-vagas.txt. Prioridade: SP, RJ, PR, SC, RS, MG, depois demais UFs.
Salva um CSV por combinação em data/bronze/.

Modo recomendado (CHROME_MODO=anexar):
  1. Feche o Chrome
  2. Rode ./iniciar_chrome.sh
  3. No Glassdoor, faça login com "Continuar com Google" (Firebase)
  4. Rode python coleta_glassdoor.py
"""

import ast
import json
import os
import platform
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
KEYWORDS_FILE = BASE_DIR / "palavras-chave-vagas.txt"
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"
OUTPUT_DIR = BRONZE_DIR
GLASSDOOR_URL = "https://www.glassdoor.com.br/index.htm"
GLASSDOOR_VAGAS_URL = "https://www.glassdoor.com.br/Job/index.htm"
GLASSDOOR_LOGIN_URL = "https://www.glassdoor.com.br/profile/login_input.htm"

MAX_VAGAS_POR_BUSCA = 50  # limite por busca (palavra-chave + localização)
VAGAS_POR_PAGINA = 30
PAUSA_ENTRE_ACOES = 2
PAUSA_APOS_PAGINACAO = 5
PAUSA_APOS_BUSCA = 4

LOCALIZACOES_PRIORITARIAS = ["SP", "RJ", "PR", "SC", "RS", "MG"]

LOCALIZACOES_RESTANTES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "PA", "PB", "PE", "PI", "RN", "RO", "RR", "SE", "TO", "Brasil",
]


def localizacoes_ordenadas() -> list[str]:
    """UFs por prioridade de volume de vagas, sem duplicatas."""
    ordenadas: list[str] = []
    vistos: set[str] = set()
    for uf in LOCALIZACOES_PRIORITARIAS + LOCALIZACOES_RESTANTES:
        if uf not in vistos:
            ordenadas.append(uf)
            vistos.add(uf)
    return ordenadas

# Glassdoor não entende siglas isoladas (ex.: "AC") — precisa do nome completo
NOMES_ESTADOS = {
    "AC": "Acre, Brasil",
    "AL": "Alagoas, Brasil",
    "AP": "Amapá, Brasil",
    "AM": "Amazonas, Brasil",
    "BA": "Bahia, Brasil",
    "CE": "Ceará, Brasil",
    "DF": "Distrito Federal, Brasil",
    "ES": "Espírito Santo, Brasil",
    "GO": "Goiás, Brasil",
    "MA": "Maranhão, Brasil",
    "MT": "Mato Grosso, Brasil",
    "MS": "Mato Grosso do Sul, Brasil",
    "MG": "Minas Gerais, Brasil",
    "PA": "Pará, Brasil",
    "PB": "Paraíba, Brasil",
    "PR": "Paraná, Brasil",
    "PE": "Pernambuco, Brasil",
    "PI": "Piauí, Brasil",
    "RJ": "Rio de Janeiro, Brasil",
    "RN": "Rio Grande do Norte, Brasil",
    "RS": "Rio Grande do Sul, Brasil",
    "RO": "Rondônia, Brasil",
    "RR": "Roraima, Brasil",
    "SC": "Santa Catarina, Brasil",
    "SE": "Sergipe, Brasil",
    "SP": "São Paulo, Brasil",
    "TO": "Tocantins, Brasil",
    "Brasil": "Brasil",
}

# Capitais e cidades principais — ajuda quando a vaga não cita o nome do estado
CIDADES_POR_UF: dict[str, list[str]] = {
    "AC": ["Rio Branco", "Cruzeiro do Sul"],
    "AL": ["Maceió"],
    "AP": ["Macapá"],
    "AM": ["Manaus"],
    "BA": ["Salvador", "Feira de Santana"],
    "CE": ["Fortaleza"],
    "DF": ["Brasília"],
    "ES": ["Vitória", "Vila Velha"],
    "GO": ["Goiânia", "Aparecida de Goiânia"],
    "MA": ["São Luís", "Imperatriz"],
    "MT": ["Cuiabá", "Várzea Grande"],
    "MS": ["Campo Grande", "Dourados"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem"],
    "PA": ["Belém", "Ananindeua"],
    "PB": ["João Pessoa", "Campina Grande"],
    "PR": ["Curitiba", "Londrina", "Maringá"],
    "PE": ["Recife", "Jaboatão dos Guararapes"],
    "PI": ["Teresina"],
    "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias"],
    "RN": ["Natal"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Canoas"],
    "RO": ["Porto Velho"],
    "RR": ["Boa Vista"],
    "SC": ["Florianópolis", "Joinville", "Blumenau"],
    "SE": ["Aracaju"],
    "SP": ["São Paulo", "Campinas", "Santos", "Guarulhos", "Ribeirão Preto"],
    "TO": ["Palmas"],
}

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def carregar_palavras_chave(caminho: Path) -> list[str]:
    """Lê e normaliza as palavras-chave do arquivo de configuração."""
    conteudo = caminho.read_text(encoding="utf-8").strip()
    palavras = ast.literal_eval(conteudo)
    return [p.strip() for p in palavras if p.strip()]


def sanitizar_nome_arquivo(texto: str) -> str:
    """Gera um nome de arquivo seguro a partir de uma palavra-chave."""
    nome = re.sub(r"[^\w\-]", "_", texto.strip().lower())
    return re.sub(r"_+", "_", nome).strip("_")[:80]


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def nome_estado(uf: str) -> str:
    return NOMES_ESTADOS.get(uf, uf).split(",")[0].strip()


def estado_representado_em_texto(texto: str, uf: str) -> bool:
    """
    Verifica se o texto representa o estado buscado.
    Evita falso positivo: 'Acre' dentro de 'Acrelândia'.
    """
    t = normalizar_texto(texto)
    if not t:
        return False
    if uf == "Brasil":
        return t == "brasil" or t.endswith(", brasil") or "(brasil)" in t

    estado = normalizar_texto(nome_estado(uf))

    padroes_estado = [
        rf"^{re.escape(estado)}$",
        rf"^{re.escape(estado)},\s*brasil",
        rf"^{re.escape(estado)}\s*\(brasil\)",
        rf",\s*{re.escape(estado)}$",
        rf",\s*{re.escape(estado)},",
        rf"{re.escape(estado)}\s*\(brasil\)",
    ]
    if any(re.search(p, t) for p in padroes_estado):
        return True

    if uf == "DF" and ("brasilia" in t or "distrito federal" in t):
        return True

    for cidade in CIDADES_POR_UF.get(uf, []):
        c = normalizar_texto(cidade)
        if re.search(rf"^{re.escape(c)}(\s*,|\s*\(|\s|$)", t):
            return True
        if re.search(rf",\s*{re.escape(c)}(\s*,|\s*\(|\s|$)", t):
            return True

    return False


def pontuar_sugestao_local(texto: str, uf: str) -> int:
    """Pontua sugestões do autocomplete — prioriza o estado, não cidades parecidas."""
    t = normalizar_texto(texto)
    if not t:
        return 0
    if uf == "Brasil":
        return 100 if "brasil" in t and "acrelandia" not in t else 0

    estado = normalizar_texto(nome_estado(uf))
    local_completo = normalizar_texto(NOMES_ESTADOS.get(uf, ""))

    if t == local_completo or t == estado:
        return 100
    if re.search(rf"^{re.escape(estado)}(\s*,\s*brasil|\s*\(brasil\))", t):
        return 95
    if re.search(rf",\s*{re.escape(estado)}$", t):
        return 90

    for cidade in CIDADES_POR_UF.get(uf, []):
        c = normalizar_texto(cidade)
        if re.search(rf"^{re.escape(c)}(\s*,|\s*\(|\s|$)", t):
            return 75

    return 0


def salvar_csv(vagas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(vagas).to_csv(caminho, index=False)
    print(f"  → {len(vagas)} vagas salvas em {caminho.name}")


# ---------------------------------------------------------------------------
# Interação com o Glassdoor
# ---------------------------------------------------------------------------


class ColetorGlassdoor:
    XPATH_CARD = '//*[@id="left-column"]/div[2]/ul/li[{n}]'
    XPATH_BOTAO_MAIS = '//*[@id="left-column"]/div[2]/div/button'
    XPATH_BUSCA_CARGO = '//*[@id="searchBar-jobTitle"]'
    XPATH_BUSCA_LOCAL = '//*[@id="searchBar-location"]'
    CLASSE_POPUP = "icon-button_IconButton__nMTOc"
    SELETORES_CARDS = [
        "#left-column li[data-test='jobListing']",
        "#left-column [data-test='jobListing']",
        "#left-column ul li",
    ]
    SELETORES_TITULO_CARD = [
        "[data-test='job-link']",
        "[data-test='job-title']",
        "a[class*='JobCard_jobTitle']",
        "a[href*='job']",
        "h2",
    ]
    SELETORES_EMPRESA_CARD = [
        "[data-test='employer-name']",
        "[class*='EmployerInfo']",
        "[class*='employerName']",
    ]
    SELETORES_LOCAL_CARD = [
        "[data-test='emp-location']",
        "[data-test='job-location']",
        "[class*='location']",
    ]
    SELETORES_SALARIO_CARD = [
        "[data-test='detailSalary']",
        "[class*='Salary']",
        "[class*='salary']",
    ]
    SELETORES_DATA_CARD = [
        "[data-test='job-age']",
        "[class*='jobAge']",
        "[class*='listing-age']",
    ]

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def _pausa(self, segundos: float = PAUSA_ENTRE_ACOES) -> None:
        time.sleep(segundos)

    def fechar_popup(self) -> None:
        popups = self.driver.find_elements(By.CLASS_NAME, self.CLASSE_POPUP)
        if popups:
            popups[0].click()
            self._pausa()

    def limpar_campo(self, elemento) -> None:
        elemento.click()
        self._pausa(0.2)
        tecla = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL
        elemento.send_keys(tecla, "a")
        elemento.send_keys(Keys.BACKSPACE)
        try:
            elemento.clear()
        except Exception:
            pass

    def _ler_valor_campo(self, campo) -> str:
        return (campo.get_attribute("value") or campo.text or "").strip()

    def _local_confirmado_no_campo(self, campo, uf: str) -> bool:
        return estado_representado_em_texto(self._ler_valor_campo(campo), uf)

    def _selecionar_sugestao_local(self, campo, uf: str) -> bool:
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: any(
                    el.is_displayed()
                    for el in d.find_elements(
                        By.CSS_SELECTOR,
                        "[role='listbox'] [role='option'], "
                        "[role='listbox'] li, "
                        "[class*='autocomplete'] li, "
                        "[class*='suggestion']",
                    )
                )
            )
        except TimeoutException:
            return False

        self._pausa(0.5)
        seletores = [
            "[role='listbox'] [role='option']",
            "[role='listbox'] li",
            "[class*='autocomplete'] li",
            "[class*='suggestion']",
            "[class*='dropdown'] li",
        ]
        sugestoes = []
        for seletor in seletores:
            sugestoes.extend(self.driver.find_elements(By.CSS_SELECTOR, seletor))

        melhor = None
        melhor_pontuacao = 0
        for sugestao in sugestoes:
            if not sugestao.is_displayed():
                continue
            pontuacao = pontuar_sugestao_local(sugestao.text, uf)
            if pontuacao > melhor_pontuacao:
                melhor_pontuacao = pontuacao
                melhor = sugestao

        if melhor and melhor_pontuacao >= 75:
            melhor.click()
            self._pausa(1)
            return True

        return False

    def _preencher_localizacao(self, uf: str) -> bool:
        local = self._local_para_busca(uf)
        campo_local = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH_BUSCA_LOCAL))
        )

        self.limpar_campo(campo_local)
        self._pausa(0.3)

        # Texto completo ajuda o autocomplete a sugerir o estado, não cidades parecidas
        campo_local.send_keys(local)
        self._pausa(1.5)

        selecionou = self._selecionar_sugestao_local(campo_local, uf)

        if not selecionou:
            self.limpar_campo(campo_local)
            campo_local.send_keys(nome_estado(uf))
            self._pausa(1.5)
            selecionou = self._selecionar_sugestao_local(campo_local, uf)

        if not selecionou:
            campo_local.send_keys(Keys.ARROW_DOWN)
            self._pausa(0.3)
            campo_local.send_keys(Keys.ENTER)
            self._pausa(1)

        campo_local.send_keys(Keys.TAB)
        self._pausa(0.5)

        valor = self._ler_valor_campo(campo_local)
        confirmado = self._local_confirmado_no_campo(campo_local, uf)
        print(f"    Local no formulário: '{valor}' {'✓' if confirmado else '✗'}")

        if not confirmado:
            print(
                f"    Esperado: estado '{nome_estado(uf)}' "
                f"(evitando cidades como Acrelândia)"
            )

        self.fechar_popup()
        return confirmado

    def _preencher_palavra_chave(self, palavra_chave: str) -> None:
        campo_cargo = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, self.XPATH_BUSCA_CARGO))
        )
        self.limpar_campo(campo_cargo)
        campo_cargo.send_keys(palavra_chave)
        self._pausa(0.5)

    def _clicar_botao_buscar(self) -> bool:
        seletores = [
            "[data-test='search-bar-submit']",
            "button[type='submit']",
            "//button[contains(@class, 'search')]",
            "//button[contains(., 'Pesquisar')]",
            "//button[contains(., 'Search')]",
        ]
        for seletor in seletores:
            by = By.XPATH if seletor.startswith("//") else By.CSS_SELECTOR
            for botao in self.driver.find_elements(by, seletor):
                if botao.is_displayed() and botao.is_enabled():
                    try:
                        botao.click()
                        self._pausa(PAUSA_APOS_BUSCA)
                        return True
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", botao)
                            self._pausa(PAUSA_APOS_BUSCA)
                            return True
                        except Exception:
                            continue
        return False

    def _submeter_busca(self) -> None:
        if self._clicar_botao_buscar():
            return
        campo_cargo = self.driver.find_element(By.XPATH, self.XPATH_BUSCA_CARGO)
        campo_cargo.send_keys(Keys.ENTER)
        self._pausa(PAUSA_APOS_BUSCA)

    def _elemento_visivel(self, by: By, seletor: str) -> bool:
        elementos = self.driver.find_elements(by, seletor)
        return bool(elementos) and elementos[0].is_displayed()

    def _botao_google_visivel(self) -> bool:
        seletores_google = [
            '//button[contains(., "Google")]',
            '//button[contains(., "google")]',
            '//*[contains(text(), "Continuar com o Google")]',
            '//*[contains(text(), "Continue with Google")]',
            '//*[contains(text(), "Entrar com o Google")]',
            '//*[contains(text(), "Sign in with Google")]',
        ]
        return any(
            self._elemento_visivel(By.XPATH, xpath) for xpath in seletores_google
        )

    def _precisa_login(self) -> bool:
        """Indicadores de que o usuário ainda não está autenticado."""
        if self._botao_google_visivel():
            return True

        seletores_entrar = [
            '//a[contains(@href, "login")]',
            '//button[contains(., "Entrar")]',
            '//a[contains(., "Entrar")]',
            '//button[contains(., "Sign In")]',
            '//a[contains(., "Sign In")]',
        ]
        return any(
            self._elemento_visivel(By.XPATH, xpath) for xpath in seletores_entrar
        )

    def _ja_esta_logado(self) -> bool:
        """Verifica sessão ativa (login Google/Firebase no Glassdoor)."""
        if self._precisa_login():
            return False

        seletores_conta = [
            '[data-test="avatar"]',
            '[data-test="profile-dropdown"]',
            '//*[@id="userDropdown"]',
            '//button[contains(@aria-label, "Perfil")]',
            '//button[contains(@aria-label, "Profile")]',
            '//img[contains(@alt, "profile")]',
        ]
        for seletor in seletores_conta:
            by = By.CSS_SELECTOR if not seletor.startswith("/") else By.XPATH
            if self._elemento_visivel(by, seletor):
                return True

        try:
            tem_firebase = self.driver.execute_script(
                """
                const keys = Object.keys(localStorage);
                return keys.some(k =>
                    k.toLowerCase().includes('firebase') ||
                    k.toLowerCase().includes('gd_') ||
                    k.toLowerCase().includes('glassdoor')
                );
                """
            )
            if tem_firebase and not self._precisa_login():
                return True
        except Exception:
            pass

        return False

    def _instrucoes_login_google(self) -> None:
        print("\n" + "=" * 60)
        print("LOGIN MANUAL — CONTA GOOGLE (Firebase)")
        print("=" * 60)
        print("No Chrome aberto, faça o login MANUALMENTE (não pelo script):")
        print(f"  1. Acesse: {GLASSDOOR_URL}")
        print("  2. Clique em 'Entrar' ou 'Sign In'")
        print("  3. Escolha 'Continuar com Google' / 'Sign in with Google'")
        print("  4. Selecione sua conta Google e conclua o login Firebase")
        print(f"  5. Confirme que está em: {GLASSDOOR_VAGAS_URL}")
        print("  6. Volte aqui e pressione Enter")
        print("=" * 60 + "\n")

    def aguardar_login(
        self, email: str | None = None, *, modo_anexar: bool = False
    ) -> None:
        """Aguarda login manual via conta Google (Firebase)."""
        try:
            self.driver.maximize_window()
        except Exception:
            pass

        if modo_anexar:
            try:
                print(f"Aba atual do Chrome: {self.driver.current_url}")
            except Exception:
                pass

            self._instrucoes_login_google()
            input("Pressione Enter quando estiver logado no Glassdoor... ")
        else:
            self.driver.get(GLASSDOOR_URL)
            self._pausa(3)

            if self._ja_esta_logado():
                print("Sessão ativa detectada — login não necessário.")
                return

            self._instrucoes_login_google()
            input("Pressione Enter quando estiver logado no Glassdoor... ")

        self.driver.get(GLASSDOOR_VAGAS_URL)
        self._pausa(3)

        if self._precisa_login():
            print(
                "\nAviso: ainda parece haver botão de login/Google na página.\n"
                "Se a coleta falhar, refaça o login manualmente no Chrome.\n"
            )

        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, self.XPATH_BUSCA_CARGO))
        )
        print("Página de vagas carregada. Iniciando coleta...\n")

    def _local_para_busca(self, uf: str) -> str:
        return NOMES_ESTADOS.get(uf, f"{uf}, Brasil")

    def _listar_cards_visiveis(self) -> list:
        for seletor in self.SELETORES_CARDS:
            encontrados = self.driver.find_elements(By.CSS_SELECTOR, seletor)
            cards = [
                c for c in encontrados
                if c.is_displayed() and len(c.text.strip()) > 15
            ]
            if cards:
                return cards
        return []

    def _primeiro_texto(self, raiz, seletores: list[str]) -> str:
        for seletor in seletores:
            for elemento in raiz.find_elements(By.CSS_SELECTOR, seletor):
                texto = elemento.text.strip()
                if texto:
                    return texto
        return ""

    def _selecionar_autocomplete(self, campo) -> None:
        """Mantido por compatibilidade — use _selecionar_sugestao_local."""
        self._selecionar_sugestao_local(campo, "Brasil")

    def _pagina_sem_vagas(self) -> bool:
        texto = self.driver.page_source.lower()
        indicadores = [
            "nenhuma vaga",
            "no jobs found",
            "0 vagas",
            "não encontramos",
        ]
        return any(t in texto for t in indicadores)

    def _aguardar_resultados_busca(self, timeout: float = 20) -> bool:
        fim = time.time() + timeout
        while time.time() < fim:
            if self._listar_cards_visiveis():
                return True
            if self._pagina_sem_vagas():
                return False
            time.sleep(0.5)
        return bool(self._listar_cards_visiveis())

    def _log_diagnostico_busca(self, palavra_chave: str, localizacao: str) -> None:
        print(f"    Diagnóstico: URL={self.driver.current_url}")
        print(f"    Busca: '{palavra_chave}' em '{self._local_para_busca(localizacao)}'")
        for seletor in self.SELETORES_CARDS:
            total = len(self.driver.find_elements(By.CSS_SELECTOR, seletor))
            if total:
                print(f"    Seletor '{seletor}': {total} elemento(s)")

    def _buscar_por_url(self, palavra_chave: str, localizacao: str) -> bool:
        local = self._local_para_busca(localizacao)
        params = urllib.parse.urlencode(
            {
                "sc.keyword": palavra_chave,
                "locKeyword": local,
                "clickSource": "searchBtn",
            }
        )
        self.driver.get(f"{GLASSDOOR_VAGAS_URL}?{params}")
        self._pausa(PAUSA_APOS_BUSCA)
        self.fechar_popup()
        return self._aguardar_resultados_busca()

    def preparar_uf(self, localizacao: str) -> bool:
        """Abre a página de vagas e define a localização da UF (uma vez por estado)."""
        self.driver.get(GLASSDOOR_VAGAS_URL)
        self._pausa(PAUSA_ENTRE_ACOES)
        local_ok = self._preencher_localizacao(localizacao)
        if local_ok:
            print(f"    UF {localizacao} ({nome_estado(localizacao)}) pronta para buscas.")
        return local_ok

    def buscar_palavra_chave(self, palavra_chave: str, localizacao: str) -> bool:
        """Busca uma palavra-chave com a localização já definida no formulário."""
        self._preencher_palavra_chave(palavra_chave)
        self._submeter_busca()
        self.fechar_popup()

        if self._aguardar_resultados_busca():
            return True

        print("    Formulário sem cards — tentando busca direta por URL...")
        if self._buscar_por_url(palavra_chave, localizacao):
            return True

        self._log_diagnostico_busca(palavra_chave, localizacao)
        return False

    def buscar(self, palavra_chave: str, localizacao: str) -> bool:
        """Busca completa: redefine localização + palavra-chave (uso avulso)."""
        self.driver.get(GLASSDOOR_VAGAS_URL)
        self._pausa(PAUSA_ENTRE_ACOES)

        local_ok = self._preencher_localizacao(localizacao)
        if not local_ok:
            print("    Aviso: localização pode não ter sido aplicada no formulário.")

        return self.buscar_palavra_chave(palavra_chave, localizacao)

    def _carregar_mais_vagas(self) -> bool:
        seletores_botao = [
            self.XPATH_BOTAO_MAIS,
            "//button[contains(., 'Mostrar mais')]",
            "//button[contains(., 'Show more')]",
        ]
        for seletor in seletores_botao:
            by = By.XPATH
            botoes = self.driver.find_elements(by, seletor)
            if botoes and botoes[0].is_displayed():
                try:
                    botoes[0].click()
                    self._pausa(PAUSA_APOS_PAGINACAO)
                    self.fechar_popup()
                    return True
                except Exception:
                    continue
        return False

    def _vaga_vazia(self, palavra_chave: str, uf_buscada: str) -> dict:
        return {
            "Palavra-chave": palavra_chave,
            "UF buscada": uf_buscada,
            "Local buscado": self._local_para_busca(uf_buscada),
            "Funcao": "",
            "Localização": "",
            "Empresa": "",
            "Data de Publicacao": "",
            "Skills Necessarias": "NF",
            "Média Salarial": "NF",
        }

    def extrair_vaga_do_card(self, card, palavra_chave: str, uf_buscada: str) -> dict:
        """Extrai dados visíveis no card da listagem (sem depender do painel lateral)."""
        vaga = self._vaga_vazia(palavra_chave, uf_buscada)
        vaga["Funcao"] = self._primeiro_texto(card, self.SELETORES_TITULO_CARD)
        vaga["Empresa"] = self._primeiro_texto(card, self.SELETORES_EMPRESA_CARD)
        vaga["Localização"] = self._primeiro_texto(card, self.SELETORES_LOCAL_CARD)
        vaga["Média Salarial"] = self._primeiro_texto(card, self.SELETORES_SALARIO_CARD) or "NF"
        vaga["Data de Publicacao"] = self._primeiro_texto(card, self.SELETORES_DATA_CARD)

        if not vaga["Funcao"]:
            linhas = [l.strip() for l in card.text.split("\n") if l.strip()]
            if len(linhas) >= 2:
                vaga["Empresa"] = vaga["Empresa"] or linhas[0]
                vaga["Funcao"] = linhas[1] if len(linhas) > 1 else ""
            if len(linhas) >= 3 and not vaga["Localização"]:
                vaga["Localização"] = linhas[2]

        return vaga

    def _obter_card(self, indice: int):
        """Busca o card pelo índice, sempre fresco no DOM (evita stale element)."""
        for _ in range(3):
            cards = self._listar_cards_visiveis()
            if indice >= len(cards):
                return None
            card = cards[indice]
            try:
                card.is_displayed()
                return card
            except StaleElementReferenceException:
                self._pausa(0.5)
        return None

    def _clicar_card(self, card) -> bool:
        self.fechar_popup()
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", card
            )
        except StaleElementReferenceException:
            return False

        self._pausa(0.5)

        for seletor in [
            "a[data-test='job-link']",
            "a[href*='job']",
            "a[href*='vaga']",
            "a",
        ]:
            try:
                links = card.find_elements(By.CSS_SELECTOR, seletor)
            except StaleElementReferenceException:
                return False

            for link in links:
                if not link.is_displayed():
                    continue
                try:
                    ActionChains(self.driver).move_to_element(link).click().perform()
                    self._pausa(2)
                    return True
                except StaleElementReferenceException:
                    return False
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", link)
                        self._pausa(2)
                        return True
                    except Exception:
                        continue

        try:
            self.driver.execute_script("arguments[0].click();", card)
            self._pausa(2)
            return True
        except StaleElementReferenceException:
            return False
        except Exception:
            return False

    def _processar_card(self, indice: int, palavra_chave: str, localizacao: str) -> dict | None:
        """Extrai e complementa uma vaga, com retry em caso de DOM atualizado."""
        for tentativa in range(3):
            card = self._obter_card(indice)
            if card is None:
                return None

            try:
                vaga = self.extrair_vaga_do_card(card, palavra_chave, localizacao)

                card = self._obter_card(indice)
                if card and self._clicar_card(card):
                    self._complementar_vaga_detalhe(vaga)

                return vaga
            except StaleElementReferenceException:
                if tentativa < 2:
                    self._pausa(0.5)
                    continue
                print(f"    Card {indice + 1}: elemento obsoleto após {tentativa + 1} tentativas.")
                return None

        return None

    def _complementar_vaga_detalhe(self, vaga: dict) -> None:
        """Preenche campos faltantes a partir do painel de detalhes, se aberto."""
        if not vaga["Funcao"]:
            vaga["Funcao"] = self._primeiro_texto(
                self.driver,
                [
                    "[class*='JobDetails_jobDetailsHeader']",
                    "[data-test='job-title']",
                    "h1",
                ],
            )

        if not vaga["Localização"]:
            vaga["Localização"] = self._primeiro_texto(
                self.driver,
                [
                    "[class*='JobDetails_location']",
                    "[data-test='emp-location']",
                    "[data-test='job-location']",
                ],
            )

        if not vaga["Empresa"]:
            vaga["Empresa"] = self._primeiro_texto(
                self.driver,
                [
                    "[class*='EmployerProfile_employerInfo']",
                    "[data-test='employerName']",
                    "[data-test='employer-name']",
                ],
            )

        if vaga["Média Salarial"] == "NF":
            salario = self._primeiro_texto(
                self.driver,
                [
                    "[data-test='detailSalary']",
                    "[class*='Salary_estimate']",
                    "[class*='salary']",
                ],
            )
            if salario:
                vaga["Média Salarial"] = salario

        descricao = self._primeiro_texto(
            self.driver,
            [
                "[class*='JobDetails_jobDetailsSection']",
                "[data-test='jobDescriptionText']",
                "#JobDescriptionContainer",
                "[class*='jobDescription']",
            ],
        )
        if descricao:
            vaga["Skills Necessarias"] = descricao

    def coletar_vagas(self, palavra_chave: str, localizacao: str) -> list[dict]:
        vagas: list[dict] = []
        indice = 0

        while indice < MAX_VAGAS_POR_BUSCA:
            if self._obter_card(indice) is None:
                if not self._carregar_mais_vagas():
                    break
                if self._obter_card(indice) is None:
                    break

            vaga = self._processar_card(indice, palavra_chave, localizacao)

            if vaga and (vaga["Funcao"] or vaga["Empresa"]):
                vagas.append(vaga)
            elif indice < 3:
                print(f"    Card {indice + 1}: dados não extraídos")

            indice += 1

            if indice % VAGAS_POR_PAGINA == 0 and not self._carregar_mais_vagas():
                break

        if not vagas:
            self._log_diagnostico_busca(palavra_chave, localizacao)

        return vagas


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------


def chrome_user_data_sistema() -> Path:
    """Diretório User Data padrão do Chrome instalado no sistema."""
    sistema = platform.system()
    home = Path.home()

    if sistema == "Darwin":
        return home / "Library/Application Support/Google/Chrome"
    if sistema == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        return Path(local) / "Google/Chrome/User Data"
    return home / ".config/google-chrome"


def chrome_user_data_coleta() -> Path:
    """Diretório dedicado à coleta (não é o padrão do sistema)."""
    return BASE_DIR / ".chrome-debug"


def resolver_user_data_dir(caminho: str | None = None) -> Path:
    if caminho:
        data_path = Path(caminho).expanduser()
        if not data_path.is_absolute():
            data_path = BASE_DIR / data_path
    else:
        data_path = chrome_user_data_coleta()

    return data_path.resolve()


def validar_user_data_dir(data_path: Path) -> None:
    """
    O Chrome bloqueia remote debugging no diretório padrão do sistema.
    """
    if data_path.resolve() == chrome_user_data_sistema().resolve():
        raise SystemExit(
            "CHROME_USER_DATA_DIR aponta para o Chrome padrão do sistema.\n"
            "O remote debugging NÃO funciona nesse diretório.\n\n"
            "Use o perfil dedicado da coleta (padrão):\n"
            f"  CHROME_USER_DATA_DIR={chrome_user_data_coleta()}\n"
            f"  CHROME_PROFILE_DIRECTORY=Default\n\n"
            "Na primeira execução, faça login com Google nesse Chrome dedicado.\n"
            "A sessão ficará salva em .chrome-debug/ para as próximas vezes."
        )


def porta_debug_ativa(porta: int) -> bool:
    """Verifica se o Chrome expõe a API de remote debugging."""
    url = f"http://127.0.0.1:{porta}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=2) as resposta:
            dados = json.loads(resposta.read().decode())
            return "Browser" in dados
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False


def aguardar_porta_debug(porta: int, tentativas: int = 15, intervalo: float = 1.0) -> bool:
    for _ in range(tentativas):
        if porta_debug_ativa(porta):
            return True
        time.sleep(intervalo)
    return False


def comando_iniciar_chrome(porta: int) -> str:
    user_data = str(
        resolver_user_data_dir(os.environ.get("CHROME_USER_DATA_DIR", "").strip() or None)
    )
    profile = os.environ.get("CHROME_PROFILE_DIRECTORY", "Default").strip()

    if platform.system() == "Darwin":
        chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        return (
            f'"{chrome_bin}" --remote-debugging-port={porta} '
            f'--remote-allow-origins=* '
            f'--user-data-dir="{user_data}" --profile-directory="{profile}"'
        )

    return (
        f'google-chrome --remote-debugging-port={porta} '
        f'--remote-allow-origins=* '
        f'--user-data-dir="{user_data}" --profile-directory="{profile}"'
    )


def aguardar_chrome_debug(porta: int) -> None:
    comando = comando_iniciar_chrome(porta)

    print("=" * 60)
    print("CHROME NÃO DETECTADO — siga estes passos:")
    print("=" * 60)
    print("1. Feche TODAS as janelas do Chrome (Cmd+Q no macOS).")
    print("2. Em outro terminal, rode:")
    print(f"\n   ./iniciar_chrome.sh\n")
    print("   Ou copie e cole:")
    print(f"\n   {comando}\n")
    print("3. No Chrome aberto, faça login no Glassdoor com 'Continuar com Google'.")
    print("4. Volte aqui e pressione Enter.")
    print("=" * 60 + "\n")
    input("Pressione Enter quando o Chrome estiver aberto... ")

    print("Verificando conexão com o Chrome...")
    if not aguardar_porta_debug(porta):
        raise SystemExit(
            f"Chrome com debug na porta {porta} não detectado.\n"
            "Confirme que:\n"
            "  - O Chrome foi iniciado com ./iniciar_chrome.sh (não abriu manualmente)\n"
            "  - Nenhuma outra janela do Chrome estava aberta antes\n"
            "  - A porta 9222 não está em uso por outro processo"
        )


def criar_driver_anexar(porta: int) -> webdriver.Chrome:
    if not porta_debug_ativa(porta):
        aguardar_chrome_debug(porta)

    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{porta}")
    print(f"Conectado ao Chrome na porta {porta} (sem flag de automação).\n")
    return webdriver.Chrome(options=options)


def criar_driver_abrir() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")

    user_data_dir = os.environ.get("CHROME_USER_DATA_DIR", "").strip()
    profile_directory = os.environ.get("CHROME_PROFILE_DIRECTORY", "Default").strip()

    data_path = resolver_user_data_dir(user_data_dir or None)
    validar_user_data_dir(data_path)
    data_path.mkdir(parents=True, exist_ok=True)

    options.add_argument(f"--user-data-dir={data_path}")
    options.add_argument(f"--profile-directory={profile_directory}")
    print(f"Perfil Chrome: {data_path / profile_directory}")
    print("Feche todas as janelas do Chrome antes de continuar.\n")

    return webdriver.Chrome(options=options)


def criar_driver() -> tuple[webdriver.Chrome, str]:
    modo = os.environ.get("CHROME_MODO", "anexar").strip().lower()
    porta = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))

    if modo == "anexar":
        return criar_driver_anexar(porta), modo

    if modo == "abrir":
        print(
            "Modo 'abrir': o Glassdoor pode exibir verificação anti-bot.\n"
            "Prefira CHROME_MODO=anexar e use ./iniciar_chrome.sh\n"
        )
        return criar_driver_abrir(), modo

    raise SystemExit(f"CHROME_MODO inválido: '{modo}'. Use 'anexar' ou 'abrir'.")


def main() -> None:
    load_dotenv(BASE_DIR / ".env")

    email = os.environ.get("GLASSDOOR_EMAIL", "").strip() or None

    palavras_chave = carregar_palavras_chave(KEYWORDS_FILE)
    localizacoes = localizacoes_ordenadas()
    total_buscas = len(palavras_chave) * len(localizacoes)

    print(f"Palavras-chave: {len(palavras_chave)}")
    print(f"Localizações:   {len(localizacoes)} (prioridade: {', '.join(LOCALIZACOES_PRIORITARIAS)})")
    print(f"Total de buscas: {total_buscas}")
    print(f"Estratégia: por UF → todas as palavras-chave")
    print(f"Camada: bronze (dados brutos)")
    print(f"Saída:  {OUTPUT_DIR}\n")

    for pasta in (BRONZE_DIR, SILVER_DIR, GOLD_DIR):
        pasta.mkdir(parents=True, exist_ok=True)

    driver, modo_chrome = criar_driver()
    coletor = ColetorGlassdoor(driver)

    try:
        coletor.aguardar_login(email, modo_anexar=(modo_chrome == "anexar"))

        busca_atual = 0
        for localizacao in localizacoes:
            print(f"\n{'=' * 60}")
            print(f"UF: {localizacao} — {nome_estado(localizacao)}")
            print(f"{'=' * 60}")

            coletor.preparar_uf(localizacao)

            for palavra_chave in palavras_chave:
                busca_atual += 1
                nome_chave = sanitizar_nome_arquivo(palavra_chave)
                arquivo = OUTPUT_DIR / f"{nome_chave}_{localizacao}.csv"

                print(
                    f"[{busca_atual}/{total_buscas}] "
                    f"{localizacao} → '{palavra_chave}'"
                )

                encontrou_resultados = coletor.buscar_palavra_chave(
                    palavra_chave, localizacao
                )
                if not encontrou_resultados:
                    print("    Nenhum resultado para esta busca.")
                try:
                    vagas = coletor.coletar_vagas(palavra_chave, localizacao)
                    salvar_csv(vagas, arquivo)
                except Exception as erro:
                    print(f"    Erro na coleta de '{palavra_chave}' em {localizacao}: {erro}")
                    print("    Continuando para a próxima busca...")

    finally:
        if modo_chrome == "anexar":
            print("\nColeta finalizada. O Chrome permanece aberto.")
        else:
            driver.quit()
            print("\nColeta finalizada.")


if __name__ == "__main__":
    main()
