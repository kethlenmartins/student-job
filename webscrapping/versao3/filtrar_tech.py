"""Classifica vagas Silver em tech, ambigua e nao_tech antes do enriquecimento.

O critério de inclusão reproduz a lógica histórica de ``analytics/scp_01``:
o título normalizado é comparado com os termos da aba ``palavras_chave`` da
planilha de critérios. A aba ``blacklist`` separa conflitos para auditoria.
"""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
CRITERIOS_PADRAO = BASE_DIR / "criterios-2026.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def normalizar_cargo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    for original, substituto in (("/", " / "), ("|", " | "), (".", " . "),
                                 ("(", " ( "), (")", " ) "), ("[", " [ "),
                                 ("]", " ] "), (":", " : "), ("-", " - "),
                                 (",", " , ")):
        texto = texto.replace(original, substituto)
    texto = re.sub(r"\s*\(\s*[aAoO]\s*\)\s*", " ", texto)
    return f" {texto} "


def termo_normalizado(valor: object) -> str:
    # No scp_01 a preparação de separadores é aplicada somente ao Cargo;
    # as palavras-chave entram no regex apenas sem acento e em minúsculas.
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()


def termos_que_casam(texto: str, termos: list[tuple[str, str]]) -> list[str]:
    encontrados: list[str] = []
    for exibicao, padrao in termos:
        try:
            if re.search(f" {padrao} ", texto):
                encontrados.append(exibicao)
        except re.error as erro:
            raise ValueError(f"Termo inválido nos critérios: {exibicao!r}: {erro}") from erro
    return encontrados


def _indice_coluna(referencia: str) -> int:
    letras = "".join(c for c in referencia if c.isalpha())
    resultado = 0
    for letra in letras:
        resultado = resultado * 26 + ord(letra.upper()) - ord("A") + 1
    return resultado - 1


def ler_aba_xlsx(arquivo: Path, numero_aba: int) -> list[dict[str, str]]:
    """Leitor mínimo das abas de critérios, sem exigir openpyxl."""
    with ZipFile(arquivo) as xlsx:
        shared = ET.fromstring(xlsx.read("xl/sharedStrings.xml"))
        strings = ["".join(item.itertext()) for item in shared.findall("m:si", NS)]
        planilha = ET.fromstring(xlsx.read(f"xl/worksheets/sheet{numero_aba}.xml"))
    linhas: list[list[str]] = []
    for linha in planilha.findall(".//m:sheetData/m:row", NS):
        valores: dict[int, str] = {}
        for celula in linha.findall("m:c", NS):
            valor = celula.find("m:v", NS)
            bruto = valor.text if valor is not None else ""
            if celula.get("t") == "s" and bruto:
                bruto = strings[int(bruto)]
            valores[_indice_coluna(celula.get("r", "A1"))] = bruto
        if valores:
            linhas.append([valores.get(i, "") for i in range(max(valores) + 1)])
    if not linhas:
        return []
    cabecalho = linhas[0]
    return [{nome: linha[i] if i < len(linha) else "" for i, nome in enumerate(cabecalho)} for linha in linhas[1:]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Triagem tech por título antes do enriquecimento")
    parser.add_argument("--input-file", type=Path, required=True, help="CSV Silver de entrada")
    parser.add_argument("--criterios", type=Path, default=CRITERIOS_PADRAO)
    parser.add_argument("--output-dir", type=Path, help="Pasta das filas (default: pasta da entrada)")
    args = parser.parse_args()
    entrada = args.input_file.resolve()
    criterios = args.criterios.resolve()
    saida = (args.output_dir or entrada.parent).resolve()
    if not entrada.exists() or not criterios.exists():
        parser.error("--input-file e --criterios devem existir")
    saida.mkdir(parents=True, exist_ok=True)

    palavras = ler_aba_xlsx(criterios, 1)
    blacklist = ler_aba_xlsx(criterios, 2)
    palavras.sort(key=lambda linha: float(linha.get("Prioridade") or "inf"))
    termos_tech = [(linha["Cargo"], termo_normalizado(linha["Cargo"])) for linha in palavras if linha.get("Cargo", "").strip()]
    termos_blacklist = [(linha["Termo"], termo_normalizado(linha["Termo"])) for linha in blacklist if linha.get("Termo", "").strip()]
    hash_criterios = hashlib.sha256(criterios.read_bytes()).hexdigest()

    with entrada.open(encoding="utf-8", newline="") as arquivo:
        campos = list(csv.DictReader(arquivo).fieldnames or [])
    if "Funcao" not in campos:
        parser.error("A entrada precisa ter a coluna Funcao")
    extras = ["source_index", "classe_triagem", "termos_tech_encontrados", "termos_blacklist_encontrados", "versao_criterios"]
    campos_saida = [x for x in campos if x not in extras] + extras
    destinos = {
        classe: (saida / f"fila_{classe}.csv").open("w", encoding="utf-8", newline="")
        for classe in ("tech", "ambigua", "nao_tech")
    }
    writers = {classe: csv.DictWriter(arquivo, fieldnames=campos_saida, extrasaction="ignore") for classe, arquivo in destinos.items()}
    for writer in writers.values():
        writer.writeheader()
    totais = {classe: 0 for classe in destinos}
    try:
        with entrada.open(encoding="utf-8", newline="") as arquivo:
            for indice, linha in enumerate(csv.DictReader(arquivo)):
                cargo = normalizar_cargo(linha.get("Funcao", ""))
                tech = termos_que_casam(cargo, termos_tech)
                bloqueios = termos_que_casam(cargo, termos_blacklist)
                classe = "tech" if tech and not bloqueios else "ambigua" if tech else "nao_tech"
                linha.update({
                    "source_index": indice,
                    "classe_triagem": classe,
                    "termos_tech_encontrados": " | ".join(tech),
                    "termos_blacklist_encontrados": " | ".join(bloqueios),
                    "versao_criterios": hash_criterios,
                })
                writers[classe].writerow(linha)
                totais[classe] += 1
    finally:
        for arquivo in destinos.values():
            arquivo.close()
    relatorio = {"input_file": str(entrada), "criterios": str(criterios), "versao_criterios": hash_criterios,
                 "totais": totais, "total": sum(totais.values())}
    (saida / "relatorio_triagem.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
