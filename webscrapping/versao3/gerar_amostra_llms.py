"""
Classifica vagas que citam LLMs específicos na descrição e exporta análise.

LLMs detectados: Claude, ChatGPT, Cursor, Gemini, Deepseek, Kimi, Grok, Ollama

Saída: amostras-analise/llms.xlsx
  - Resumo        : contagem por LLM × área
  - <LLM>         : todas as vagas que citam aquele LLM (com trecho de contexto)
  - Co-ocorrência : quais LLMs aparecem juntos na mesma vaga
"""

import re
import pandas as pd
from pathlib import Path
from unidecode import unidecode

BASE = Path(__file__).resolve().parent
DATA = BASE / "analytics" / "data"
OUT  = BASE / "amostras-analise"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Carrega dados
# ---------------------------------------------------------------------------
print("Carregando dados...")
df2 = pd.read_csv(DATA / "scp_02.csv")
df3 = pd.read_csv(DATA / "scp_03.csv")

df = df3[["Cargo", "area", "tipo", "nivel", "estado", "salario", "IA"]].copy()
df["Skills"] = df2["Skills"].values
df.rename(columns={"area": "Area", "tipo": "Tipo", "nivel": "Nivel",
                    "estado": "Estado", "salario": "Salario"}, inplace=True)

# ---------------------------------------------------------------------------
# Mesma função de limpeza do scp_03
# ---------------------------------------------------------------------------
def clean_text_search(text):
    if not isinstance(text, str):
        return ""
    text = text.replace("C++", "cplusplus").replace("c++", "cplusplus")
    text = text.replace("C#", "csharp").replace("c#", "csharp")
    text = unidecode(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s#+.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

df["Skills_Search"] = df["Skills"].fillna("").apply(clean_text_search)

# ---------------------------------------------------------------------------
# Padrões por LLM
# ---------------------------------------------------------------------------
LLMS = {
    "Claude":    r"\bclaude\b",
    "ChatGPT":   r"\b(chatgpt|chat gpt)\b",
    "Cursor":    r"\bcursor\b",
    "Gemini":    r"\bgemini\b",
    "Deepseek":  r"\b(deepseek|deep seek)\b",
    "Kimi":      r"\bkimi\b",
    "Grok":      r"\bgrok\b",
    "Ollama":    r"\bollama\b",
}

# ---------------------------------------------------------------------------
# Função para extrair trecho de contexto ao redor do match
# ---------------------------------------------------------------------------
def extrair_contexto(texto_limpo, padrao, janela=80):
    m = re.search(padrao, texto_limpo)
    if not m:
        return ""
    start = max(0, m.start() - janela)
    end   = min(len(texto_limpo), m.end() + janela)
    return f"...{texto_limpo[start:end]}..."

# ---------------------------------------------------------------------------
# Aplica detecção
# ---------------------------------------------------------------------------
print("Detectando menções a LLMs...")
for llm, pat in LLMS.items():
    col = f"llm_{llm.lower()}"
    df[col] = df["Skills_Search"].str.contains(pat, regex=True, na=False).astype(int)

llm_cols = [f"llm_{n.lower()}" for n in LLMS]

# ---------------------------------------------------------------------------
# Exporta
# ---------------------------------------------------------------------------
COLS_BASE = ["Cargo", "Area", "Tipo", "Nivel", "Estado", "Salario", "IA", "Skills"]

print("Exportando llms.xlsx...")
with pd.ExcelWriter(OUT / "llms.xlsx", engine="openpyxl") as writer:

    # --- Aba Resumo: contagem por LLM e por área ---
    areas = sorted(df["Area"].dropna().unique())
    resumo_rows = []
    for llm in LLMS:
        col = f"llm_{llm.lower()}"
        total = df[col].sum()
        row = {"LLM": llm, "Total vagas": total}
        for area in areas:
            row[area] = int(df.loc[df["Area"] == area, col].sum())
        row["% do total (15514)"] = round(total / len(df) * 100, 2)
        row["% vagas com IA=1"] = round(
            df.loc[df["IA"] == 1, col].sum() / max(df["IA"].sum(), 1) * 100, 2
        )
        resumo_rows.append(row)
    df_resumo = pd.DataFrame(resumo_rows).sort_values("Total vagas", ascending=False)
    df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
    print(f"  Resumo gerado")

    # --- Uma aba por LLM ---
    for llm, pat in LLMS.items():
        col = f"llm_{llm.lower()}"
        vagas = df[df[col] == 1].copy()

        if vagas.empty:
            print(f"  {llm}: 0 vagas — aba pulada")
            continue

        vagas["contexto"] = vagas["Skills_Search"].apply(
            lambda t: extrair_contexto(t, pat)
        )
        # Quais outros LLMs também aparecem nessa vaga
        vagas["outros_llms"] = vagas[llm_cols].apply(
            lambda row: ", ".join(
                name for name, c in zip(LLMS.keys(), llm_cols)
                if name != llm and row[c] == 1
            ), axis=1
        )

        export_cols = COLS_BASE + ["contexto", "outros_llms"]
        vagas[export_cols].to_excel(writer, sheet_name=llm, index=False)
        print(f"  {llm}: {len(vagas)} vagas")

    # --- Aba Co-ocorrência ---
    print("  Calculando co-ocorrências...")
    co_rows = []
    llm_names = list(LLMS.keys())
    for i, a in enumerate(llm_names):
        for b in llm_names[i+1:]:
            col_a = f"llm_{a.lower()}"
            col_b = f"llm_{b.lower()}"
            n = int((df[col_a] & df[col_b]).sum())
            if n > 0:
                co_rows.append({"LLM A": a, "LLM B": b, "Vagas com ambos": n})
    df_co = pd.DataFrame(co_rows).sort_values("Vagas com ambos", ascending=False)
    df_co.to_excel(writer, sheet_name="Co-ocorrência", index=False)

    # --- Aba Visão geral por área (vagas com qualquer LLM) ---
    df["qualquer_llm"] = df[llm_cols].max(axis=1)
    dist_area = df.groupby("Area").agg(
        total_vagas=("Cargo", "count"),
        vagas_com_llm=("qualquer_llm", "sum")
    ).reset_index()
    dist_area["% com LLM"] = (dist_area["vagas_com_llm"] / dist_area["total_vagas"] * 100).round(1)
    dist_area.to_excel(writer, sheet_name="Por área", index=False)

print(f"\nArquivo salvo em: {OUT / 'llms.xlsx'}")
print(f"\n=== Resumo ===")
for _, r in df_resumo.iterrows():
    print(f"  {r['LLM']:10s}: {int(r['Total vagas']):4d} vagas  ({r['% do total (15514)']:.1f}%)")
