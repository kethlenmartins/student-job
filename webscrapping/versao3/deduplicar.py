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

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
OUTPUT_FILE = SILVER_DIR / "vagas_unicas.csv"


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
    arquivos = sorted(BRONZE_DIR.glob("*.csv"))
    print(f"Arquivos bronze encontrados: {len(arquivos):,}")

    if not arquivos:
        print(f"Nenhum arquivo CSV encontrado em {BRONZE_DIR}")
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

    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df_unicas.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSalvo em: {OUTPUT_FILE}")

    # Mostra divisões sugeridas para enriquecer.py (16 terminais: 8 máquinas × 2)
    n = len(df_unicas)
    q, resto = divmod(n, 16)
    limites = []
    start = 0
    for i in range(16):
        fim = start + q + (1 if i < resto else 0)
        limites.append((start, fim))
        start = fim

    pessoas   = ["MacBook Kethlen", "MacBook Kethlen", "PC Inteli Kethlen", "PC Inteli Kethlen",
                 "Luana", "Luana", "Tati", "Tati",
                 "Lucas", "Lucas", "PC Inteli Marco", "PC Inteli Marco",
                 "PC Inteli Scarpelin", "PC Inteli Scarpelin", "Leo", "Leo"]
    maquinas  = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8]
    terminais = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]

    print(f"\n{'=' * 75}")
    print("Índices para enriquecer.py  (16 terminais — 8 máquinas × 2):")
    print(f"{'=' * 75}")
    for i, ((ini, fim), maq, term, pessoa) in enumerate(zip(limites, maquinas, terminais, pessoas)):
        perf = f"e{i + 1}"
        print(f"  M{maq} T{term}  {pessoa:<22}  --perfil chrome-profile-{perf:<4}  --inicio {ini:<7} --fim {fim}")
    print(f"{'=' * 75}")


if __name__ == "__main__":
    main()
