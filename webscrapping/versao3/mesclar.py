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
import argparse
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SILVER_DIR = BASE_DIR / "data" / "silver"
OUTPUT_FILE = SILVER_DIR / "vagas_enriquecidas.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mescla resultados do enriquecimento")
    parser.add_argument("--run-id", help="Lê data/runs/<id>/silver/")
    args = parser.parse_args()
    silver_dir = SILVER_DIR
    output_file = OUTPUT_FILE
    if args.run_id:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.run_id):
            parser.error("run-id inválido; use letras, números, _ ou -")
        silver_dir = BASE_DIR / "data" / "runs" / args.run_id / "silver"
        output_file = silver_dir / "vagas_enriquecidas.csv"
    # Aceita tanto o formato legado quanto os resultados incrementais da
    # versão paralela. Não misture os dois para a mesma fatia, pois ambos
    # representam as mesmas vagas.
    arquivos = sorted(silver_dir.glob("enriquecido_*.csv"))
    print(f"Arquivos encontrados: {len(arquivos)}")

    if not arquivos:
        print(f"Nenhum arquivo enriquecido_*.csv em {silver_dir}")
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

    # Um processo interrompido e retomado pode ter uma linha antiga seguida
    # da nova para o mesmo source_index. Mantém a última, sem descartar vagas
    # de intervalos diferentes.
    if "source_index" in df_final.columns:
        paralelo = df_final[df_final["source_index"].notna()]
        legado = df_final[df_final["source_index"].isna()]
        antes = len(paralelo)
        paralelo = paralelo.drop_duplicates(subset="source_index", keep="last")
        df_final = pd.concat([legado, paralelo], ignore_index=True)
        if len(paralelo) != antes:
            print(f"Retomadas consolidadas: {antes - len(paralelo):,} linhas antigas removidas")

    com_desc = df_final["Skills Necessarias"].ne("NF").sum()
    sem_desc = df_final["Skills Necessarias"].eq("NF").sum()

    print(f"\nTotal: {len(df_final):,} vagas")
    print(f"  Com descrição: {com_desc:,} ({com_desc/len(df_final)*100:.1f}%)")
    print(f"  Sem descrição: {sem_desc:,} ({sem_desc/len(df_final)*100:.1f}%)")

    df_final.to_csv(output_file, index=False)
    print(f"\nSalvo em: {output_file}")


if __name__ == "__main__":
    main()
