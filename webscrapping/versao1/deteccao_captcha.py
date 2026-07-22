"""
Heurísticas para detectar verificação anti-bot / captcha no Glassdoor.

Usado pelo testar_deteccao_captcha.py para mapear em qual busca/etapa
a detecção é acionada.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By

# ---------------------------------------------------------------------------
# Padrões conhecidos (URL, título, texto, DOM)
# ---------------------------------------------------------------------------

PADROES_URL = [
    r"captcha",
    r"challenge",
    r"verify",
    r"blocked",
    r"robot",
    r"security[-_]?check",
    r"unusual[-_]?activity",
    r"access[-_]?denied",
]

PADROES_TITULO = [
    r"verify",
    r"verifica",
    r"robot",
    r"rob[oô]",
    r"security",
    r"seguran",
    r"captcha",
    r"blocked",
    r"bloquead",
    r"access denied",
    r"acesso negado",
    r"just a moment",
    r"um momento",
]

# Padrões em texto sem acento (_normalizar aplica antes da busca)
PADROES_TEXTO_PAGINA = [
    r"verify you are human",
    r"confirm you(?:'re| are) human",
    r"prove you(?:'re| are) (?:not a )?robot",
    r"not a robot",
    r"unusual traffic",
    r"before we continue",
    r"security check",
    r"access (?:has been )?denied",
    r"confirme que voce e humano",
    r"nao e um robo",
    r"trafego incomum",
    r"antes de continuar",
    r"verificacao de seguran",
    r"detectamos atividade incomum",
    r"precisamos verificar",
    r"complete a verifica",
    r"resolva o captcha",
    r"marque a caixa",
    r"i'?m not a robot",
]

SELETORES_DOM = [
    ("iframe_recaptcha", "iframe[src*='recaptcha']"),
    ("iframe_google", "iframe[src*='google.com/recaptcha']"),
    ("iframe_turnstile", "iframe[src*='challenges.cloudflare']"),
    ("iframe_turnstile2", "iframe[src*='turnstile']"),
    (
        "div_captcha",
        "div[id*='captcha'], div[id*='Captcha'], "
        "div[class*='captcha'], div[class*='Captcha']",
    ),
    ("g_recaptcha", ".g-recaptcha, #g-recaptcha"),
    ("hcaptcha", "iframe[src*='hcaptcha']"),
    ("challenge_form", "form[action*='captcha'], form[id*='challenge']"),
]

# Sinais fracos — sozinhos não disparam alerta, mas somam contexto
PADROES_FRACOS = [
    r"cloudflare",
    r"cf-browser-verification",
    r"datadome",
    r"perimeterx",
    r"arkose",
    r"funcaptcha",
]


def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def _buscar_padroes(texto: str, padroes: list[str]) -> list[str]:
    t = _normalizar(texto)
    return [p for p in padroes if re.search(p, t, re.IGNORECASE)]


@dataclass
class ResultadoDeteccao:
    detectado: bool
    confianca: str  # alta | media | baixa | nenhuma
    etapa: str
    busca_numero: int | None
    palavra_chave: str | None
    uf: str | None
    url: str
    titulo: str
    motivos: list[str] = field(default_factory=list)
    sinais_fracos: list[str] = field(default_factory=list)
    elementos_dom: list[str] = field(default_factory=list)
    tem_barra_busca: bool = False
    qtd_cards_vagas: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def para_dict(self) -> dict:
        return asdict(self)


def _contar_cards(driver: webdriver.Chrome) -> int:
    seletores = [
        "#left-column li[data-test='jobListing']",
        "#left-column [data-test='jobListing']",
        "#left-column ul li",
    ]
    for seletor in seletores:
        elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
        visiveis = [e for e in elementos if e.is_displayed() and len(e.text.strip()) > 15]
        if visiveis:
            return len(visiveis)
    return 0


def _tem_barra_busca(driver: webdriver.Chrome) -> bool:
    try:
        campo = driver.find_elements(By.CSS_SELECTOR, "#searchBar-jobTitle, #searchBar-location")
        return any(e.is_displayed() for e in campo)
    except Exception:
        return False


def avaliar_pagina(
    driver: webdriver.Chrome,
    *,
    etapa: str,
    busca_numero: int | None = None,
    palavra_chave: str | None = None,
    uf: str | None = None,
    espera_resultados: bool = False,
) -> ResultadoDeteccao:
    """
    Avalia a página atual e retorna sinais de captcha/anti-bot.

    espera_resultados=True: ausência de barra de busca + cards conta como suspeita.
    """
    url = ""
    titulo = ""
    try:
        url = driver.current_url or ""
        titulo = driver.title or ""
    except Exception:
        pass

    motivos: list[str] = []
    sinais_fracos: list[str] = []
    elementos_dom: list[str] = []

    for nome, seletor in SELETORES_DOM:
        try:
            encontrados = driver.find_elements(By.CSS_SELECTOR, seletor)
            if any(e.is_displayed() for e in encontrados):
                elementos_dom.append(nome)
                motivos.append(f"DOM: {nome}")
        except Exception:
            continue

    for padrao in _buscar_padroes(url, PADROES_URL):
        motivos.append(f"URL: /{padrao}/")

    for padrao in _buscar_padroes(titulo, PADROES_TITULO):
        motivos.append(f"Título: /{padrao}/")

    try:
        texto_visivel = driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        texto_visivel = ""

    for padrao in _buscar_padroes(texto_visivel, PADROES_TEXTO_PAGINA):
        motivos.append(f"Texto: /{padrao}/")

    try:
        html = driver.page_source or ""
    except Exception:
        html = ""

    for padrao in _buscar_padroes(html, PADROES_FRACOS):
        sinais_fracos.append(padrao)

    tem_busca = _tem_barra_busca(driver)
    qtd_cards = _contar_cards(driver)

    if espera_resultados and not motivos:
        if not tem_busca and not qtd_cards:
            motivos.append("Página de vagas sem barra de busca e sem cards")
        elif not qtd_cards and any(
            p in _normalizar(texto_visivel)
            for p in ("verificar", "verify", "captcha", "robot", "robô")
        ):
            motivos.append("Sem cards de vaga com texto de verificação na página")

    # Confiança
    confianca = "nenhuma"
    detectado = False

    sinais_fortes = (
        elementos_dom
        or any(m.startswith(("URL:", "Texto:")) for m in motivos)
        or len([m for m in motivos if m.startswith("Título:")]) >= 1
        and not tem_busca
    )

    if elementos_dom or any(m.startswith("Texto:") for m in motivos):
        confianca = "alta"
        detectado = True
    elif any(m.startswith("URL:") for m in motivos):
        confianca = "alta"
        detectado = True
    elif sinais_fortes and not qtd_cards and not tem_busca:
        confianca = "media"
        detectado = True
    elif motivos and not qtd_cards:
        confianca = "media"
        detectado = True
    elif sinais_fracos and not tem_busca and not qtd_cards:
        confianca = "baixa"
        detectado = True

    return ResultadoDeteccao(
        detectado=detectado,
        confianca=confianca,
        etapa=etapa,
        busca_numero=busca_numero,
        palavra_chave=palavra_chave,
        uf=uf,
        url=url,
        titulo=titulo,
        motivos=motivos,
        sinais_fracos=sinais_fracos,
        elementos_dom=elementos_dom,
        tem_barra_busca=tem_busca,
        qtd_cards_vagas=qtd_cards,
    )


def salvar_screenshot(driver: webdriver.Chrome, destino: Path) -> Path | None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        if driver.save_screenshot(str(destino)):
            return destino
    except Exception:
        pass
    return None


def registrar_evento(
    resultado: ResultadoDeteccao,
    journal: Path,
    *,
    screenshot: Path | None = None,
) -> None:
    journal.parent.mkdir(parents=True, exist_ok=True)
    linha = resultado.para_dict()
    if screenshot:
        linha["screenshot"] = str(screenshot)
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
