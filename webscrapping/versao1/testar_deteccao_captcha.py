#!/usr/bin/env python3
"""
Testa em qual busca/etapa o Glassdoor aciona verificação anti-bot.

Não coleta vagas — só executa buscas e registra quando a detecção dispara.

Uso:
  1. ./iniciar_chrome.sh
  2. Login manual no Glassdoor
  3. python testar_deteccao_captcha.py

Exemplos:
  python testar_deteccao_captcha.py --max-buscas 15 --uf SP
  python testar_deteccao_captcha.py --estrategia batch --pausa 8
  python testar_deteccao_captcha.py --estrategia ciclo --max-buscas 30
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from coleta_glassdoor import (
    BASE_DIR,
    KEYWORDS_FILE,
    LOCALIZACOES_PRIORITARIAS,
    carregar_palavras_chave,
    criar_driver,
    localizacoes_ordenadas,
    nome_estado,
)
from coleta_glassdoor import ColetorGlassdoor
from deteccao_captcha import (
    avaliar_pagina,
    registrar_evento,
    salvar_screenshot,
)

PROBES_DIR = BASE_DIR / "data" / "captcha-probes"
JOURNAL_PATH = PROBES_DIR / "journal.jsonl"


def _slug(texto: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in texto)[:40].strip("_")


def _imprimir_resultado(resultado, *, destaque: bool = False) -> None:
    prefixo = "!!! CAPTCHA/ANTI-BOT" if resultado.detectado else "ok"
    busca = resultado.busca_numero if resultado.busca_numero is not None else "-"
    uf = resultado.uf or "-"
    palavra = resultado.palavra_chave or "-"

    linha = (
        f"  [{prefixo}] busca={busca} etapa={resultado.etapa} "
        f"uf={uf} palavra='{palavra}' "
        f"conf={resultado.confianca} cards={resultado.qtd_cards_vagas}"
    )
    if destaque:
        print("\n" + "=" * 60)
    print(linha)
    if resultado.motivos:
        print(f"    motivos: {', '.join(resultado.motivos)}")
    if resultado.sinais_fracos:
        print(f"    sinais fracos: {', '.join(resultado.sinais_fracos)}")
    if resultado.elementos_dom:
        print(f"    DOM: {', '.join(resultado.elementos_dom)}")
    print(f"    url: {resultado.url[:100]}")
    print(f"    título: {resultado.titulo[:80]}")
    if destaque:
        print("=" * 60 + "\n")


def _checar_e_registrar(
    driver,
    coletor: ColetorGlassdoor,
    *,
    etapa: str,
    busca_numero: int | None,
    palavra_chave: str | None,
    uf: str | None,
    espera_resultados: bool,
    pausar_ao_detectar: bool,
) -> bool:
    """Retorna True se detectou captcha/anti-bot."""
    resultado = avaliar_pagina(
        driver,
        etapa=etapa,
        busca_numero=busca_numero,
        palavra_chave=palavra_chave,
        uf=uf,
        espera_resultados=espera_resultados,
    )

    screenshot = None
    if resultado.detectado:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = f"{stamp}_b{busca_numero or 0}_{_slug(etapa)}_{uf or 'xx'}.png"
        screenshot = salvar_screenshot(driver, PROBES_DIR / "screenshots" / nome)

    registrar_evento(resultado, JOURNAL_PATH, screenshot=screenshot)
    _imprimir_resultado(resultado, destaque=resultado.detectado)

    if resultado.detectado and pausar_ao_detectar:
        print(
            "\nDetecção registrada. Resolva manualmente no Chrome se necessário.\n"
            f"Screenshot: {screenshot or 'falhou'}\n"
            f"Journal:    {JOURNAL_PATH}\n"
        )
        input("Pressione Enter para continuar o teste (ou Ctrl+C para parar)... ")

        # Reavalia após intervenção manual
        pos = avaliar_pagina(
            driver,
            etapa=f"{etapa}_apos_pausa",
            busca_numero=busca_numero,
            palavra_chave=palavra_chave,
            uf=uf,
            espera_resultados=espera_resultados,
        )
        registrar_evento(pos, JOURNAL_PATH)
        _imprimir_resultado(pos)

    return resultado.detectado


def executar_teste(args: argparse.Namespace) -> int:
    load_dotenv(BASE_DIR / ".env")

    palavras = carregar_palavras_chave(KEYWORDS_FILE)
    if args.max_palavras:
        palavras = palavras[: args.max_palavras]

    if args.uf:
        ufs = [args.uf.upper()]
    else:
        ufs = localizacoes_ordenadas()[: args.max_ufs]

    combinacoes: list[tuple[str, str]] = []
    for uf in ufs:
        for palavra in palavras:
            combinacoes.append((uf, palavra))
            if len(combinacoes) >= args.max_buscas:
                break
        if len(combinacoes) >= args.max_buscas:
            break

    PROBES_DIR.mkdir(parents=True, exist_ok=True)
    resumo_path = PROBES_DIR / "resumo_ultimo_teste.json"

    print("=" * 60)
    print("TESTE DE DETECÇÃO CAPTCHA / ANTI-BOT — Glassdoor")
    print("=" * 60)
    print(f"Buscas planejadas: {len(combinacoes)}")
    print(f"Estratégia:        {args.estrategia}")
    print(f"Pausa entre buscas:{args.pausa}s")
    print(f"UFs:               {', '.join(ufs)}")
    print(f"Journal:           {JOURNAL_PATH}")
    print(f"Screenshots:       {PROBES_DIR / 'screenshots'}")
    print("=" * 60 + "\n")

    driver, modo_chrome = criar_driver()
    coletor = ColetorGlassdoor(driver)

    deteccoes: list[dict] = []
    busca_numero = 0

    try:
        coletor.aguardar_login(modo_anexar=(modo_chrome == "anexar"))

        _checar_e_registrar(
            driver,
            coletor,
            etapa="apos_login",
            busca_numero=None,
            palavra_chave=None,
            uf=None,
            espera_resultados=False,
            pausar_ao_detectar=args.pausar_ao_detectar,
        )

        uf_atual: str | None = None

        for uf, palavra_chave in combinacoes:
            busca_numero += 1
            print(f"\n--- Busca {busca_numero}/{len(combinacoes)}: {uf} → '{palavra_chave}' ---")

            if args.estrategia == "batch":
                if uf != uf_atual:
                    uf_atual = uf
                    print(f"  preparar_uf({uf}) — {nome_estado(uf)}")
                    coletor.preparar_uf(uf)
                    if _checar_e_registrar(
                        driver,
                        coletor,
                        etapa="apos_preparar_uf",
                        busca_numero=busca_numero,
                        palavra_chave=palavra_chave,
                        uf=uf,
                        espera_resultados=True,
                        pausar_ao_detectar=args.pausar_ao_detectar,
                    ):
                        deteccoes.append({"busca": busca_numero, "etapa": "apos_preparar_uf", "uf": uf})

                coletor.buscar_palavra_chave(palavra_chave, uf)
            else:
                coletor.buscar(palavra_chave, uf)

            detectou = _checar_e_registrar(
                driver,
                coletor,
                etapa="apos_busca",
                busca_numero=busca_numero,
                palavra_chave=palavra_chave,
                uf=uf,
                espera_resultados=True,
                pausar_ao_detectar=args.pausar_ao_detectar,
            )
            if detectou:
                deteccoes.append({"busca": busca_numero, "etapa": "apos_busca", "uf": uf, "palavra": palavra_chave})

            if args.pausa > 0 and busca_numero < len(combinacoes):
                time.sleep(args.pausa)

    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário.")
    finally:
        if modo_chrome == "anexar":
            print("\nChrome permanece aberto.")
        else:
            driver.quit()

    resumo = {
        "timestamp": datetime.now().isoformat(),
        "estrategia": args.estrategia,
        "total_buscas": busca_numero,
        "deteccoes": deteccoes,
        "journal": str(JOURNAL_PATH),
    }
    resumo_path.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("RESUMO DO TESTE")
    print("=" * 60)
    print(f"Buscas executadas: {busca_numero}")
    print(f"Detecções:         {len(deteccoes)}")
    if deteccoes:
        for d in deteccoes:
            print(f"  - busca {d['busca']} ({d['etapa']}) uf={d.get('uf')} palavra={d.get('palavra', '-')}")
    else:
        print("  Nenhuma detecção nesta execução.")
    print(f"\nDetalhes em: {JOURNAL_PATH}")
    print(f"Resumo em:     {resumo_path}")
    print("=" * 60)

    return 1 if deteccoes else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mapeia em qual busca o Glassdoor aciona captcha/anti-bot."
    )
    parser.add_argument(
        "--max-buscas",
        type=int,
        default=20,
        help="Número máximo de buscas (UF + palavra-chave) a executar (padrão: 20)",
    )
    parser.add_argument(
        "--max-palavras",
        type=int,
        default=None,
        help="Limita quantas palavras-chave do arquivo usar",
    )
    parser.add_argument(
        "--max-ufs",
        type=int,
        default=1,
        help="Quantas UFs testar, em ordem de prioridade (padrão: 1 = só SP)",
    )
    parser.add_argument(
        "--uf",
        type=str,
        default=None,
        help="Testar apenas uma UF (ex.: SP, RJ)",
    )
    parser.add_argument(
        "--estrategia",
        choices=("ciclo", "batch"),
        default="ciclo",
        help=(
            "ciclo = busca completa por vez (UF+palavra); "
            "batch = preparar_uf uma vez e trocar só palavra-chave"
        ),
    )
    parser.add_argument(
        "--pausa",
        type=float,
        default=5.0,
        help="Segundos entre buscas (padrão: 5)",
    )
    parser.add_argument(
        "--sem-pausar-ao-detectar",
        action="store_true",
        help="Não pausar para resolução manual quando detectar captcha",
    )

    args = parser.parse_args()
    args.pausar_ao_detectar = not args.sem_pausar_ao_detectar

    if args.uf and args.uf.upper() not in {*LOCALIZACOES_PRIORITARIAS, "Brasil"}:
        # aceita qualquer sigla válida; só avisa se parecer estranha
        pass

    sys.exit(executar_teste(args))


if __name__ == "__main__":
    main()
