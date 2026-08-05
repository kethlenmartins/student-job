"""Reescreve as células de matching do scp_03.ipynb para usar:
- clean_text_search (remove pontuação antes de buscar)
- correspondência com sinônimos da planilha de critérios
- regra especial para R (evita match da letra isolada)
- word boundaries (\b) em vez de espaços como delimitador
"""
import json

with open('analytics/scp_03.ipynb') as f:
    nb = json.load(f)

updates = {
    # Adiciona import re
    'b655f05b': [
        "import pandas as pd\n",
        "import re\n",
        "from unidecode import unidecode\n"
    ],

    # Substitui clean_text por clean_text_search (remove pontuação)
    '28d0d120': [
        "def clean_text_search(text):\n",
        "    if not isinstance(text, str):\n",
        "        return ''\n",
        "    text = text.replace('C++', 'cplusplus').replace('c++', 'cplusplus')\n",
        "    text = text.replace('C#', 'csharp').replace('c#', 'csharp')\n",
        "    text = unidecode(text).lower().strip()\n",
        "    text = re.sub(r'[^a-z0-9\\s#+.]', ' ', text)\n",
        "    text = re.sub(r'\\s+', ' ', text)\n",
        "    return text\n"
    ],

    # Prepara coluna de busca e carrega sinônimos
    'ad24ccc7': [
        "df['Skills_Search'] = df['Skills'].fillna('').apply(clean_text_search)\n",
        "df_skills['Sinônimos'] = df_skills['Sinônimos'].fillna('').astype(str)\n"
    ],

    # Loop principal: skill + sinônimos + regra especial para R
    'c3108d21': [
        "print('Iniciando identificação de skills com sinônimos...')\n",
        "\n",
        "for _, row in df_skills.iterrows():\n",
        "    skill_name = row['Skill']\n",
        "    synonyms_str = str(row['Sinônimos'])\n",
        "\n",
        "    # Nome da coluna baseado no nome principal da skill\n",
        "    col_name = 'sk_' + clean_text_search(skill_name).replace(' ', '_')\n",
        "    df[col_name] = 0\n",
        "\n",
        "    # Monta lista: skill principal + sinônimos\n",
        "    terms = [skill_name]\n",
        "    if synonyms_str.strip():\n",
        "        terms.extend(re.split(r'[;,|]', synonyms_str))\n",
        "    clean_terms = [clean_text_search(t) for t in terms if t.strip()]\n",
        "\n",
        "    # Regra especial para R (evita match da letra isolada)\n",
        "    if skill_name.strip().lower() == 'r':\n",
        "        pattern = r'\\b(r language|linguagem r|programacao r|r studio|rstudio)\\b'\n",
        "    else:\n",
        "        pattern = r'\\b(' + '|'.join(map(re.escape, clean_terms)) + r')\\b'\n",
        "\n",
        "    mask = df['Skills_Search'].str.contains(pattern, regex=True, na=False)\n",
        "    df.loc[mask, col_name] = 1\n",
        "\n",
        "print('Identificação concluída.')\n"
    ],

    # IA loop: usa Skills_Search + word boundaries
    '79c6136e': [
        "df['IA'] = 0\n",
        "\n",
        "for _, row in df_IA.iterrows():\n",
        "    palavra_clean = clean_text_search(str(row['Palavra']))\n",
        "    if not palavra_clean.strip():\n",
        "        continue\n",
        "    pattern = r'\\b' + re.escape(palavra_clean.strip()) + r'\\b'\n",
        "    mask = df['Skills_Search'].str.contains(pattern, regex=True, na=False)\n",
        "    df.loc[mask, 'IA'] = 1\n"
    ],

    # Drop inclui Skills_Search
    'ed2869c0': [
        "df.drop(columns=['Skills', 'Skills_Search', 'Local Cidade', 'Local Tipo'], inplace=True)\n",
        "df.rename(columns={\n",
        "    'Area': 'area',\n",
        "    'Tipo': 'tipo',\n",
        "    'Nivel': 'nivel',\n",
        "    'Local Estado': 'estado',\n",
        "    'Salario': 'salario'\n",
        "}, inplace=True)\n"
    ],
}

updated = []
for cell in nb['cells']:
    cid = cell.get('id')
    if cid in updates:
        cell['source'] = updates[cid]
        cell['outputs'] = []
        cell['execution_count'] = None
        updated.append(cid)

with open('analytics/scp_03.ipynb', 'w') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f'Células atualizadas: {updated}')
print('Salvo.')
