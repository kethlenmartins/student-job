"""
Fase 2: Deduplicação dos CSVs da camada Bronze.

Lê todos os arquivos em data/bronze/, aplica a chave composta
(jobListingId > hash normalizado por Funcao+Empresa+Localização)
e gera data/silver/vagas_unicas.csv.

Uso:
  python deduplicar.py

Pré-requisito:
  Copiar data/bronze/ da Máquina 2 para a Máquina 1 antes de rodar.
  Ver seção "Sincronização entre máquinas" no README.
"""

import re
import unicodedata
from pathlib import Path
import argparse

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
OUTPUT_FILE = SILVER_DIR / "vagas_unicas.csv"


def diretorios_run(run_id: str | None) -> tuple[Path, Path, Path]:
    if not run_id:
        return BRONZE_DIR, SILVER_DIR, OUTPUT_FILE
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id):
        raise ValueError("run-id inválido; use letras, números, _ ou -")
    raiz = BASE_DIR / "data" / "runs" / run_id
    return raiz / "bronze", raiz / "silver", raiz / "silver" / "vagas_unicas.csv"


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def chave_vaga(row: pd.Series) -> str:
    """
    Chave de deduplicação cross-busca.
    Prioridade 1: jobListingId extraído da URL (identificador canônico do Glassdoor).
    Prioridade 2: hash de Funcao + Empresa + Localização normalizados.
    """
    url = str(row.get("URL", "") or "")
    m = re.search(r"jobListingId=(\d+)", url)
    if m:
        return f"gd:{m.group(1)}"

    funcao = normalizar_texto(str(row.get("Funcao", "") or ""))
    empresa = normalizar_texto(str(row.get("Empresa", "") or ""))
    local = normalizar_texto(str(row.get("Localização", "") or ""))
    return f"txt:{funcao}|{empresa}|{local}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicação da Bronze para Silver")
    parser.add_argument("--run-id", help="Rodada isolada em data/runs/<id>/")
    args = parser.parse_args()
    try:
        bronze_dir, silver_dir, output_file = diretorios_run(args.run_id)
    except ValueError as erro:
        parser.error(str(erro))
    arquivos = sorted(bronze_dir.glob("*.csv"))
    print(f"Arquivos bronze encontrados: {len(arquivos):,}")

    if not arquivos:
        print(f"Nenhum arquivo CSV encontrado em {bronze_dir}")
        print("Certifique-se de ter copiado os dados da Máquina 2 antes de rodar.")
        return

    frames = []
    erros = 0
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, dtype=str).fillna("")
            frames.append(df)
        except Exception as e:
            print(f"  Erro em {arq.name}: {e}")
            erros += 1

    if not frames:
        print("Nenhum dado carregado.")
        return

    print(f"Arquivos com erro: {erros}")

    df_total = pd.concat(frames, ignore_index=True)
    print(f"Registros brutos: {len(df_total):,}")

    # Remove vagas completamente vazias
    df_total = df_total[
        df_total["Funcao"].str.strip().ne("") | df_total["Empresa"].str.strip().ne("")
    ]
    print(f"Após remover vazios: {len(df_total):,}")

    df_total["_chave"] = df_total.apply(chave_vaga, axis=1)

    # Remove chaves do tipo "txt:|" (função e empresa ambos vazios após normalização)
    df_total = df_total[df_total["_chave"] != "txt:||"]

    # Dedup: mantém a primeira ocorrência de cada chave
    # (primeira = maior probabilidade de ter mais dados preenchidos, pois SP vem antes)
    df_unicas = df_total.drop_duplicates(subset="_chave", keep="first").copy()
    df_unicas = df_unicas.drop(columns="_chave")

    por_id = df_unicas["URL"].str.contains("jobListingId=", na=False).sum()
    por_texto = len(df_unicas) - por_id

    print(f"\nVagas únicas: {len(df_unicas):,}")
    print(f"  → identificadas por jobListingId: {por_id:,} ({por_id/len(df_unicas)*100:.1f}%)")
    print(f"  → identificadas por hash texto:   {por_texto:,} ({por_texto/len(df_unicas)*100:.1f}%)")
    print(f"\nSem URL (não enriquecíveis): {df_unicas['URL'].str.strip().eq('').sum():,}")

    silver_dir.mkdir(parents=True, exist_ok=True)
    df_unicas.to_csv(output_file, index=False)
    print(f"\nSalvo em: {output_file}")

    # Uma máquina usa um Chrome com várias abas; a fila limitada evita
    # multiplicar processos e perfis Chrome.
    n = len(df_unicas)
    print(f"\n{'=' * 75}")
    print("Comando sugerido para enriquecer_paralelo.py (1 Chrome × 4 abas):")
    print(f"{'=' * 75}")
    print(f"  --perfil chrome-profile-enrich --workers 4 --inicio 0 --fim {n}")
    print(f"{'=' * 75}")


if __name__ == "__main__":
    main()
