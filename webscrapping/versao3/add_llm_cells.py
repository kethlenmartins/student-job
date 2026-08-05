import json, uuid

with open('analytics/scp_04.ipynb') as f:
    nb = json.load(f)

def make_markdown(source_lines):
    return {
        "cell_type": "markdown",
        "id": str(uuid.uuid4())[:8],
        "metadata": {},
        "source": source_lines
    }

def make_code(source_lines):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": str(uuid.uuid4())[:8],
        "metadata": {},
        "outputs": [],
        "source": source_lines
    }

# --- Separador de seção ---
cell_md = make_markdown([
    "---\n",
    "## LLMs Citadas nas Vagas\n",
    "\n",
    "Detecta menções explícitas a modelos de linguagem específicos "
    "(Claude, ChatGPT, Cursor, Gemini, Deepseek, Kimi, Grok, Ollama) "
    "nas descrições das vagas."
])

# --- Carrega Skills e detecta LLMs ---
cell_load = make_code([
    "import pandas as pd\n",
    "import re\n",
    "\n",
    "# Carrega Skills do scp_02 (coluna não presente no scp_03)\n",
    "df2 = pd.read_csv('data/scp_02.csv')\n",
    "df['Skills'] = df2['Skills'].values\n",
    "df['Skills_Search'] = df['Skills'].fillna('').apply(clean_text_search)\n",
    "\n",
    "LLMS = {\n",
    "    'Claude':   r'\\bclaude\\b',\n",
    "    'ChatGPT':  r'\\b(chatgpt|chat gpt)\\b',\n",
    "    'Cursor':   r'\\bcursor\\b',\n",
    "    'Gemini':   r'\\bgemini\\b',\n",
    "    'Deepseek': r'\\b(deepseek|deep seek)\\b',\n",
    "    'Kimi':     r'\\bkimi\\b',\n",
    "    'Grok':     r'\\bgrok\\b',\n",
    "    'Ollama':   r'\\bollama\\b',\n",
    "}\n",
    "\n",
    "llm_cols = []\n",
    "for llm, pat in LLMS.items():\n",
    "    col = f'llm_{llm.lower()}'\n",
    "    df[col] = df['Skills_Search'].str.contains(pat, regex=True, na=False).astype(int)\n",
    "    llm_cols.append(col)\n",
    "\n",
    "df['qualquer_llm'] = df[llm_cols].max(axis=1)\n",
    "\n",
    "total = len(df)\n",
    "print('=== LLMs detectadas ===')\n",
    "for llm, col in zip(LLMS, llm_cols):\n",
    "    n = df[col].sum()\n",
    "    print(f'  {llm:10s}: {n:4d} vagas  ({n/total*100:.1f}%)')\n",
    "print(f'\\n  Qualquer LLM: {df[\"qualquer_llm\"].sum()} vagas ({df[\"qualquer_llm\"].sum()/total*100:.1f}%)')\n"
])

# --- Ranking geral e por área ---
cell_ranking = make_code([
    "# --- Ranking geral ---\n",
    "resumo_rows = []\n",
    "for llm, col in zip(LLMS, llm_cols):\n",
    "    n = int(df[col].sum())\n",
    "    resumo_rows.append({'LLM': llm, 'Vagas': n, '% do total': round(n/len(df)*100, 1)})\n",
    "df_resumo_llm = pd.DataFrame(resumo_rows).sort_values('Vagas', ascending=False)\n",
    "print('--- Ranking geral ---')\n",
    "display(df_resumo_llm)\n",
    "\n",
    "# --- Por área ---\n",
    "areas = df['Area'].value_counts().index.tolist()\n",
    "rows_area = []\n",
    "for llm, col in zip(LLMS, llm_cols):\n",
    "    row = {'LLM': llm}\n",
    "    for area in areas:\n",
    "        mask = df['Area'] == area\n",
    "        total_area = mask.sum()\n",
    "        n = int(df.loc[mask, col].sum())\n",
    "        row[area] = f'{n} ({n/total_area*100:.1f}%)' if total_area else '0'\n",
    "    rows_area.append(row)\n",
    "df_llm_area = pd.DataFrame(rows_area).set_index('LLM')\n",
    "print('\\n--- LLMs por área ---')\n",
    "display(df_llm_area)\n"
])

# --- Por nível de senioridade ---
cell_nivel = make_code([
    "# --- Por nível de senioridade ---\n",
    "rows_nivel = []\n",
    "for llm, col in zip(LLMS, llm_cols):\n",
    "    row = {'LLM': llm}\n",
    "    for nivel in df['Nivel'].unique():\n",
    "        mask = df['Nivel'] == nivel\n",
    "        total_nivel = mask.sum()\n",
    "        n = int(df.loc[mask, col].sum())\n",
    "        row[nivel] = f'{n} ({n/total_nivel*100:.1f}%)' if total_nivel else '0'\n",
    "    rows_nivel.append(row)\n",
    "df_llm_nivel = pd.DataFrame(rows_nivel).set_index('LLM')\n",
    "print('--- LLMs por nível de senioridade ---')\n",
    "display(df_llm_nivel)\n"
])

# --- Co-ocorrências e LLM vs IA ---
cell_co = make_code([
    "# --- Co-ocorrências ---\n",
    "llm_names = list(LLMS.keys())\n",
    "co_rows = []\n",
    "for i, a in enumerate(llm_names):\n",
    "    for b in llm_names[i+1:]:\n",
    "        col_a, col_b = f'llm_{a.lower()}', f'llm_{b.lower()}'\n",
    "        n = int((df[col_a] & df[col_b]).sum())\n",
    "        if n > 0:\n",
    "            co_rows.append({\n",
    "                'LLM A': a, 'LLM B': b, 'Vagas com ambos': n,\n",
    "                '% de A': round(n / max(df[col_a].sum(), 1) * 100, 1),\n",
    "                '% de B': round(n / max(df[col_b].sum(), 1) * 100, 1),\n",
    "            })\n",
    "df_co = pd.DataFrame(co_rows).sort_values('Vagas com ambos', ascending=False)\n",
    "print('--- Co-ocorrências entre LLMs ---')\n",
    "display(df_co)\n",
    "\n",
    "# --- LLMs vs flag IA ---\n",
    "print('\\n--- Vagas com LLM específica vs flag IA=1 ---')\n",
    "for llm, col in zip(LLMS, llm_cols):\n",
    "    llm_total = int(df[col].sum())\n",
    "    llm_com_ia = int(((df[col] == 1) & (df['IA'] == 1)).sum())\n",
    "    if llm_total > 0:\n",
    "        print(f'  {llm:10s}: {llm_total} vagas | {llm_com_ia} com IA=1 ({llm_com_ia/llm_total*100:.0f}%)')\n"
])

nb['cells'].extend([cell_md, cell_load, cell_ranking, cell_nivel, cell_co])

with open('analytics/scp_04.ipynb', 'w') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'Notebook atualizado: {len(nb["cells"])} células no total')
