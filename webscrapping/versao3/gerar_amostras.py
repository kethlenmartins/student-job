"""
Gera amostras para análise manual, exportando para XLSX em amostras-analise/.

Amostras geradas:
  1. localidade.xlsx      — foco em presencial/remoto/n/f
  2. machine_learning.xlsx — vagas com sk_machine_learning = 1
  3. sem_senioridade.xlsx  — todas as vagas sem nível detectado (nivel = n/f)
  4. ia_por_area.xlsx      — vagas com flag IA=1, amostradas por área (1 aba por área)
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "analytics" / "data"
OUT = BASE / "amostras-analise"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Carrega e mescla scp_02 (dados completos + localidade + descrição) e
# scp_03 (flags de skills + IA). Ambos têm 15.514 linhas na mesma ordem.
# ---------------------------------------------------------------------------
print("Carregando dados...")
df2 = pd.read_csv(DATA / "scp_02.csv")
df3 = pd.read_csv(DATA / "scp_03.csv")

assert len(df2) == len(df3), f"Tamanhos diferentes: scp_02={len(df2)}, scp_03={len(df3)}"

# Colunas base de cada fonte
COLS_BASE = ["Cargo", "Area", "Tipo", "Nivel", "Local Cidade", "Local Estado", "Local Tipo", "Salario", "Skills"]
COLS_SK = [c for c in df3.columns if c.startswith("sk_")]
COLS_IA = ["IA"]

# Monta DataFrame unificado
df = df2[COLS_BASE].copy()
df = pd.concat([df.reset_index(drop=True), df3[COLS_SK + COLS_IA].reset_index(drop=True)], axis=1)

print(f"Dataset unificado: {len(df)} vagas, {len(df.columns)} colunas")

# Colunas reduzidas para leitura humana (descrição + identificação + localidade + classificação)
COLS_LEITURA = ["Cargo", "Area", "Tipo", "Nivel", "Local Cidade", "Local Estado", "Local Tipo", "Salario", "Skills"]


# ---------------------------------------------------------------------------
# 1. Amostra — localidade (presencial / remoto / não classificado)
# ---------------------------------------------------------------------------
print("\n[1/4] Gerando amostra de localidade...")

remoto   = df[df["Local Tipo"] == "remoto"]
nao_enc  = df[df["Local Tipo"] == "n/e"]   # não encontrado / ambíguo
nao_det  = df[df["Local Tipo"] == "n/f"]   # não encontrado no pipeline

# Nacional: busca por termos de trabalho remoto/híbrido na descrição que foram
# classificados como presencial — candidatos a falsos negativos
hibrido_mask = (
    df["Local Tipo"] == "nacional"
) & df["Skills"].str.contains(
    r"hí?brido|home.?office|trabalho.?remoto|100%.?remoto|full.?remote|modelo.?remoto",
    case=False, na=False, regex=True
)
falsos_negativos = df[hibrido_mask].sample(n=min(100, hibrido_mask.sum()), random_state=42)

# Amostra estratificada de presencial puro (sem menção de remoto na descrição)
presencial_puro = df[
    (df["Local Tipo"] == "nacional") & ~hibrido_mask
].sample(n=min(50, (~hibrido_mask & (df["Local Tipo"] == "nacional")).sum()), random_state=42)

with pd.ExcelWriter(OUT / "localidade.xlsx", engine="openpyxl") as writer:
    remoto[COLS_LEITURA].to_excel(writer, sheet_name="Remoto (todos)", index=False)
    nao_enc[COLS_LEITURA].to_excel(writer, sheet_name="n_e (ambíguo)", index=False)
    nao_det[COLS_LEITURA].sample(n=min(200, len(nao_det)), random_state=42).to_excel(
        writer, sheet_name="n_f (200 amostra)", index=False
    )
    falsos_negativos[COLS_LEITURA].to_excel(
        writer, sheet_name="Nacional c_termo_remoto", index=False
    )
    presencial_puro[COLS_LEITURA].to_excel(
        writer, sheet_name="Presencial puro (50)", index=False
    )

print(f"  remoto={len(remoto)} | n/e={len(nao_enc)} | n/f={len(nao_det)} | "
      f"nacional c/termo_remoto={len(falsos_negativos)} | presencial={len(presencial_puro)}")


# ---------------------------------------------------------------------------
# 2. Amostra — Machine Learning
# ---------------------------------------------------------------------------
print("\n[2/4] Gerando amostra de Machine Learning...")

ml_mask = df["sk_machine_learning"] == 1
df_ml = df[ml_mask].copy()

# Skills relacionadas a ML/IA para contexto visual
SK_ML_CONTEXTO = [
    "sk_machine_learning", "sk_python", "sk_r", "sk_sql", "sk_cloud",
    "sk_aws", "sk_azure", "sk_gcp", "sk_spark", "sk_airflow", "sk_kafka",
    "sk_redes_neurais", "sk_langchain", "sk_prompt_eng.", "sk_vector_databases",
    "sk_nosql", "sk_elasticsearch", "sk_dbt", "IA",
]

COLS_ML = COLS_LEITURA + [c for c in SK_ML_CONTEXTO if c in df.columns]

with pd.ExcelWriter(OUT / "machine_learning.xlsx", engine="openpyxl") as writer:
    df_ml[COLS_ML].to_excel(writer, sheet_name="Vagas com ML", index=False)

    # Vagas de Dados/IA SEM flag ML — candidatos a falsos negativos
    dados_sem_ml = df[
        df["Area"].str.contains("Dados", na=False) & (~ml_mask)
    ].sample(n=min(150, (~ml_mask & df["Area"].str.contains("Dados", na=False)).sum()), random_state=42)
    dados_sem_ml[COLS_ML].to_excel(writer, sheet_name="Dados_IA sem ML (150)", index=False)

    # Distribuição por área
    dist = df_ml["Area"].value_counts().reset_index()
    dist.columns = ["Area", "Vagas com ML"]
    dist["% do total ML"] = (dist["Vagas com ML"] / len(df_ml) * 100).round(1)
    dist.to_excel(writer, sheet_name="Distribuição por área", index=False)

print(f"  vagas com ML={len(df_ml)} | Dados/IA sem ML (amostra)={len(dados_sem_ml)}")


# ---------------------------------------------------------------------------
# 3. Todas as vagas sem senioridade (nivel = n/f)
# ---------------------------------------------------------------------------
print("\n[3/4] Gerando amostra sem senioridade...")

df_sf = df[df["Nivel"] == "n/f"].copy()

SK_SENIORIDADE = [
    "sk_machine_learning", "sk_python", "sk_java", "sk_sql", "sk_cloud",
    "sk_ci_cd", "sk_docker", "sk_kubernetes", "sk_api", "IA",
]
COLS_SF = COLS_LEITURA + [c for c in SK_SENIORIDADE if c in df.columns]

with pd.ExcelWriter(OUT / "sem_senioridade.xlsx", engine="openpyxl") as writer:
    df_sf[COLS_SF].to_excel(writer, sheet_name="Todas sem nível", index=False)

    # Distribuição por área para dar contexto
    dist_sf = df_sf["Area"].value_counts().reset_index()
    dist_sf.columns = ["Area", "Vagas"]
    dist_sf["% dentro de n/f"] = (dist_sf["Vagas"] / len(df_sf) * 100).round(1)
    dist_sf.to_excel(writer, sheet_name="Distribuição por área", index=False)

    # Distribuição por tipo de cargo
    dist_tipo = df_sf["Tipo"].value_counts().reset_index()
    dist_tipo.columns = ["Tipo", "Vagas"]
    dist_tipo.to_excel(writer, sheet_name="Distribuição por tipo", index=False)

print(f"  vagas sem senioridade={len(df_sf)}")


# ---------------------------------------------------------------------------
# 4. Vagas com IA = 1, amostradas por área (1 aba por área + resumo geral)
# ---------------------------------------------------------------------------
print("\n[4/4] Gerando amostra de vagas IA por área...")

df_ia = df[df["IA"] == 1].copy()

SK_IA_CONTEXTO = [
    "IA", "sk_machine_learning", "sk_redes_neurais", "sk_python",
    "sk_langchain", "sk_prompt_eng.", "sk_vector_databases",
    "sk_cloud", "sk_aws", "sk_azure", "sk_gcp",
]
COLS_IA = COLS_LEITURA + [c for c in SK_IA_CONTEXTO if c in df.columns]

AMOSTRA_POR_AREA = 75

with pd.ExcelWriter(OUT / "ia_por_area.xlsx", engine="openpyxl") as writer:
    # Aba de resumo geral
    resumo = df_ia["Area"].value_counts().reset_index()
    resumo.columns = ["Area", "Vagas com IA"]
    total_area = df.groupby("Area").size().reset_index(name="Total vagas")
    resumo = resumo.merge(total_area, on="Area")
    resumo["% IA na área"] = (resumo["Vagas com IA"] / resumo["Total vagas"] * 100).round(1)
    resumo.to_excel(writer, sheet_name="Resumo", index=False)

    # Uma aba por área
    for area in df_ia["Area"].unique():
        vagas_area = df_ia[df_ia["Area"] == area]
        amostra = vagas_area.sample(
            n=min(AMOSTRA_POR_AREA, len(vagas_area)), random_state=42
        )
        # Nome de aba válido para xlsx (máx 31 chars)
        nome_aba = area.replace("e Inteligência Artificial", "e IA")
        nome_aba = nome_aba[:31]
        amostra[COLS_IA].to_excel(writer, sheet_name=nome_aba, index=False)
        print(f"  {area}: {len(vagas_area)} vagas IA → amostra {len(amostra)}")


# ---------------------------------------------------------------------------
# Resumo final
# ---------------------------------------------------------------------------
print("\n=== Amostras geradas em", OUT, "===")
for f in sorted(OUT.glob("*.xlsx")):
    print(f"  {f.name}")
