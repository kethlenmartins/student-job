"""
Fase 3 (pós-enriquecimento): Mescla os arquivos enriquecido_*.csv gerados
por cada terminal em um único data/silver/vagas_enriquecidas.csv.

Uso:
  python mesclar.py

Pré-requisito:
  Todos os terminais de enriquecer.py devem ter finalizado.
  Copiar os enriquecido_*.csv da Máquina 2 para data/silver/ da Máquina 1.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SILVER_DIR = BASE_DIR / "data" / "silver"
OUTPUT_FILE = SILVER_DIR / "vagas_enriquecidas.csv"


def main() -> None:
    arquivos = sorted(SILVER_DIR.glob("enriquecido_*.csv"))
    print(f"Arquivos encontrados: {len(arquivos)}")

    if not arquivos:
        print(f"Nenhum arquivo enriquecido_*.csv em {SILVER_DIR}")
        return

    frames = []
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, dtype=str).fillna("")
            print(f"  {arq.name}: {len(df):,} vagas")
            frames.append(df)
        except Exception as e:
            print(f"  Erro em {arq.name}: {e}")

    if not frames:
        return

    df_final = pd.concat(frames, ignore_index=True)

    com_desc = df_final["Skills Necessarias"].ne("NF").sum()
    sem_desc = df_final["Skills Necessarias"].eq("NF").sum()

    print(f"\nTotal: {len(df_final):,} vagas")
    print(f"  Com descrição: {com_desc:,} ({com_desc/len(df_final)*100:.1f}%)")
    print(f"  Sem descrição: {sem_desc:,} ({sem_desc/len(df_final)*100:.1f}%)")

    df_final.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSalvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
