# Coleta de Vagas Glassdoor 2026 — Guia de Participação

Obrigada por ajudar! Este documento explica tudo que você precisa fazer na sua
máquina para a coleta funcionar. Você não precisa ler o guia todo — só a seção
com o seu nome.

---

## O que é este projeto?

Estamos coletando dados de vagas de emprego em tecnologia do Glassdoor Brasil
para uma pesquisa de carreiras. O objetivo é entender quais habilidades,
salários e regiões aparecem mais nas vagas de tech — tudo automatizado.

Como o volume é grande (~5.400 buscas no total), dividimos o trabalho entre
várias máquinas rodando ao mesmo tempo. Cada máquina faz uma fatia das buscas
e, ao final, juntamos tudo.

---

## Como funciona o pipeline

A coleta acontece em três fases:

```
Fase 1 — Coleta         Cada máquina busca suas palavras-chave no Glassdoor
                        e salva os resultados em CSVs (pasta data/bronze/).
                        ↓ todas enviam os CSVs para a Kethlen (Slack/Drive)

Fase 2 — Deduplicação   Só a Kethlen roda. Junta todos os CSVs, remove
                        duplicatas e gera um único arquivo de vagas únicas.
                        ↓ Kethlen envia de volta para todas as máquinas

Fase 3 — Enriquecimento Cada máquina visita as páginas de cada vaga para
                        coletar a descrição completa e as skills exigidas.
                        ↓ todas enviam os resultados para a Kethlen
                        ↓ Kethlen faz o merge final
```

A coleta usa um navegador Chrome real (não headless) para evitar bloqueios
automáticos do Glassdoor. O script imita comportamento humano: delays
aleatórios, scroll, fechamento de popups.

---

## Participantes e distribuição

| Máquina | Pessoa | OS | Terminais Fase 3 |
|---------|--------|----|-----------------|
| M1 ⭐   | MacBook Kethlen *(central)* | macOS | e1–e4 |
| M2      | PC Inteli — Kethlen | Linux | e5–e8 |
| M3      | PC Inteli — Marco | Linux | e9–e12 |
| M4      | Leo | Windows | e13–e16 |

**Fase 1 concluída.** Agora estamos na Fase 3 — enriquecimento das vagas únicas.

---

## ⚠️ Regras durante a coleta (leia antes de começar)

O script roda em background, mas existem coisas que interrompem o processo.

### macOS (com tmux)

| Ação | Pode? |
|------|-------|
| Desligar a tela | ✅ Sim — configure para não suspender (ver abaixo) |
| Fechar o app Terminal | ✅ Sim — o tmux continua rodando |
| Usar o computador para outras coisas | ✅ Sim |
| Suspender / hibernar o Mac | ❌ Não — interrompe o processo |
| Fechar o laptop sem "nunca suspender" configurado | ❌ Não |
| Desligar ou reiniciar | ❌ Não |
| Fechar o terminal tmux sem desacoplar (`Ctrl+b d`) | ❌ Não |

**Para evitar suspensão automática no Mac:** use `caffeinate -i` antes do comando
`python` (incluído nos comandos abaixo). Ou: Ajustes do Sistema → Bateria →
desative "Ativar Power Nap" e defina tela como Nunca.

### Linux (com tmux)

| Ação | Pode? |
|------|-------|
| Fechar o terminal | ✅ Sim — tmux continua |
| Desligar a tela | ✅ Sim |
| Usar o computador para outras coisas | ✅ Sim |
| Suspender / hibernar | ❌ Não |
| Desligar ou reiniciar | ❌ Não |

### Windows (PowerShell)

| Ação | Pode? |
|------|-------|
| Desligar a tela | ✅ Sim — configure para nunca suspender (ver abaixo) |
| Minimizar o PowerShell | ✅ Sim |
| Usar o computador para outras coisas | ✅ Sim |
| Fechar a janela do PowerShell | ❌ Não — encerra o processo |
| Suspender, hibernar, desligar ou reiniciar | ❌ Não |

**Para evitar suspensão no Windows:** Painel de Controle → Opções de Energia →
"Colocar o computador em suspensão": **Nunca** (quando conectado).

> **Se o processo for interrompido:** não tem problema. Basta rodar o mesmo
> comando novamente — o script retoma de onde parou, pulando os CSVs que já
> existem.

---

## Pré-requisitos — antes de tudo

Antes de começar qualquer passo desta seção, você precisa ter **Git** e **Python**
instalados na sua máquina. Se já tiver os dois, pule direto para
[Clonar o repositório](#clonar-o-repositório).

---

### Instalar o Git

O Git é o programa que permite baixar o código do projeto para a sua máquina.

**macOS:**
```bash
# Opção 1 — via Homebrew (recomendado)
brew install git

# Opção 2 — via Xcode Command Line Tools
xcode-select --install
```
> Se não tiver o Homebrew: cole no terminal → `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

**Linux (Ubuntu / Debian):**
```bash
sudo apt update && sudo apt install git -y
```

**Windows:**
1. Acesse **https://git-scm.com/download/win** e baixe o instalador
2. Execute o instalador e clique em **Next** em todas as telas (as opções padrão funcionam)
3. Ao final, abra o **Git Bash** ou o **PowerShell** e confirme: `git --version`

---

### Instalar o Python

O script de coleta roda em Python 3.10 ou superior.

**macOS:**
```bash
brew install python
```

**Linux (Ubuntu / Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

**Windows:**
1. Acesse **https://www.python.org/downloads/** e baixe a versão mais recente
2. Execute o instalador; marque a opção **"Add Python to PATH"** antes de continuar
3. Clique em **Install Now**
4. Confirme no PowerShell: `python --version`

---

### Clonar o repositório

Depois de instalar o Git, baixe o código do projeto para a sua máquina.
Você só precisa fazer isso **uma vez**.

**macOS / Linux:**
```bash
git clone https://github.com/kethlenmartins/student-job.git
cd student-job
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/kethlenmartins/student-job.git
cd student-job
```

> **Onde fica o código?** Uma pasta chamada `2025-1A-T09-ES07-G02` será criada no
> diretório em que você rodou o comando. Os passos seguintes partem desse diretório.

---

## Máquina 1 — Kethlen ⭐ (máquina central)

Esta máquina faz a coleta normal (Fase 1) e também é a responsável por
centralizar os dados: receber os CSVs de todos, rodar a deduplicação e
distribuir o arquivo final para o enriquecimento (Fase 3).

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Rode cada comando abaixo em um terminal separado. Quando o Chrome abrir,
faça login no Glassdoor pelo botão "Continuar com Google" e pressione Enter
no terminal para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 13 --perfil chrome-profile-t1 --sem-enriquecer

# Terminal 2 (abrir outro terminal)
python coleta_glassdoor.py --kw-inicio 13 --kw-fim 26 --perfil chrome-profile-t2 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 13 --perfil chrome-profile-t1 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 13 --kw-fim 26 --perfil chrome-profile-t2 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
# Terminal 1
tmux new -s t1
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 0 --kw-fim 13 \
  --perfil chrome-profile-t1 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d  para desacoplar

# Terminal 2
tmux new -s t2
source venv/bin/activate
caffeinate -dims python coleta_glassdoor.py \
  --kw-inicio 13 --kw-fim 26 \
  --perfil chrome-profile-t2 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 13 --perfil chrome-profile-t1 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 13 --kw-fim 26 --perfil chrome-profile-t2 --sem-enriquecer --assume-logged-in
```

Para ver o progresso (macOS/Linux): `tmux attach -t t1`. Para desacoplar: `Ctrl+b d`.

#### Passo 3 — Verificar se terminou

O script imprime `Coleta finalizada.` ao terminar. Para confirmar pelo número de arquivos:

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **702**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **702**

---

### Entre Fase 1 e Fase 2 — Centralizar os CSVs

#### Passo 4 — Aguardar e receber os CSVs das outras máquinas

Quando cada pessoa terminar a Fase 1, ela vai te enviar os CSVs pelo Slack
(numa pasta do Drive ou os arquivos direto). Salve todos em `data/bronze/`.

> Só avance para o Passo 5 quando **todas as 4 máquinas** tiverem terminado.

#### Passo 5 — Deduplicação

**macOS / Linux:**
```bash
source venv/bin/activate
python deduplicar.py
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python deduplicar.py
```

O script vai imprimir os índices exatos para a Fase 3 de cada máquina:

```
Vagas únicas: 123.737
...
Índices para enriquecer.py  (16 terminais — 4 máquinas × 4):
===========================================================================
  M1 e1   MacBook Kethlen        --perfil chrome-profile-e1    --inicio 0       --fim 7734
  M1 e2   MacBook Kethlen        --perfil chrome-profile-e2    --inicio 7734    --fim 15468
  M1 e3   MacBook Kethlen        --perfil chrome-profile-e3    --inicio 15468   --fim 23202
  M1 e4   MacBook Kethlen        --perfil chrome-profile-e4    --inicio 23202   --fim 30936
  M2 e5   PC Inteli Kethlen      --perfil chrome-profile-e5    --inicio 30936   --fim 38670
  M2 e6   PC Inteli Kethlen      --perfil chrome-profile-e6    --inicio 38670   --fim 46404
  M2 e7   PC Inteli Kethlen      --perfil chrome-profile-e7    --inicio 46404   --fim 54138
  M2 e8   PC Inteli Kethlen      --perfil chrome-profile-e8    --inicio 54138   --fim 61872
  M3 e9   PC Inteli Marco        --perfil chrome-profile-e9    --inicio 61872   --fim 69606
  M3 e10  PC Inteli Marco        --perfil chrome-profile-e10   --inicio 69606   --fim 77339
  M3 e11  PC Inteli Marco        --perfil chrome-profile-e11   --inicio 77339   --fim 85072
  M3 e12  PC Inteli Marco        --perfil chrome-profile-e12   --inicio 85072   --fim 92805
  M4 e13  Leo                    --perfil chrome-profile-e13   --inicio 92805   --fim 100538
  M4 e14  Leo                    --perfil chrome-profile-e14   --inicio 100538  --fim 108271
  M4 e15  Leo                    --perfil chrome-profile-e15   --inicio 108271  --fim 116004
  M4 e16  Leo                    --perfil chrome-profile-e16   --inicio 116004  --fim 123737
```

#### Passo 6 — Distribuir para todas as máquinas

Envie no Slack para cada pessoa:
1. O arquivo `data/silver/vagas_unicas.csv`
2. Os índices `--inicio` e `--fim` específicos da máquina dela (copie da saída acima)

---

### Fase 3 — Enriquecimento

#### Passo 7 — Configurar perfis de enriquecimento (fazer uma vez)

Rode cada comando abaixo em um terminal separado. Quando o Chrome abrir,
confirme o login no Glassdoor e pressione Enter no terminal. Depois, encerre com Ctrl+C.

```bash
source venv/bin/activate
python enriquecer.py --inicio 0 --fim 7734 --perfil chrome-profile-e1
# (outro terminal)
python enriquecer.py --inicio 7734 --fim 15468 --perfil chrome-profile-e2
# (outro terminal)
python enriquecer.py --inicio 15468 --fim 23202 --perfil chrome-profile-e3
# (outro terminal)
python enriquecer.py --inicio 23202 --fim 30936 --perfil chrome-profile-e4
```

#### Passo 8 — Rodar o enriquecimento (4 terminais tmux)

Abra 4 terminais (ou 4 janelas tmux) e rode um bloco em cada:

```bash
tmux new -s e1
source venv/bin/activate
caffeinate -dims python3 enriquecer.py \
  --inicio 0 --fim 7734 \
  --perfil chrome-profile-e1 --assume-logged-in
# Ctrl+b d para desacoplar
```

```bash
tmux new -s e2
source venv/bin/activate
caffeinate -dims python3 enriquecer.py \
  --inicio 7734 --fim 15468 \
  --perfil chrome-profile-e2 --assume-logged-in
# Ctrl+b d para desacoplar
```

```bash
tmux new -s e3
source venv/bin/activate
caffeinate -dims python3 enriquecer.py \
  --inicio 15468 --fim 23202 \
  --perfil chrome-profile-e3 --assume-logged-in
# Ctrl+b d para desacoplar
```

```bash
tmux new -s e4
source venv/bin/activate
caffeinate -dims python3 enriquecer.py \
  --inicio 23202 --fim 30936 \
  --perfil chrome-profile-e4 --assume-logged-in
# Ctrl+b d para desacoplar
```

Para acompanhar o progresso: `tmux attach -t e1` (ou e2, e3, e4). Para desacoplar: `Ctrl+b d`.

#### Passo 9 — Aguardar todas as máquinas e fazer o merge final

Quando todas enviarem os arquivos `enriquecido_*.csv`, salve em `data/silver/` e rode:

**macOS / Linux:**
```bash
source venv/bin/activate
python mesclar.py
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python mesclar.py
```

Arquivo final: `data/silver/vagas_enriquecidas.csv`

---

---

## Máquina 2 — PC Inteli (Kethlen)

Você vai fazer a Fase 1 (coleta de vagas) e depois a Fase 3 (enriquecimento),
sempre a partir de instruções da Kethlen.

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 26 --kw-fim 39 --perfil chrome-profile-t3 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 39 --kw-fim 52 --perfil chrome-profile-t4 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 26 --kw-fim 39 --perfil chrome-profile-t3 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 39 --kw-fim 52 --perfil chrome-profile-t4 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t3
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 26 --kw-fim 39 \
  --perfil chrome-profile-t3 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t4
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 39 --kw-fim 52 \
  --perfil chrome-profile-t4 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 26 --kw-fim 39 --perfil chrome-profile-t3 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 39 --kw-fim 52 --perfil chrome-profile-t4 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

O script imprime `Coleta finalizada.` ao terminar.

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **702**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **702**

#### Passo 4 — Enviar para a Kethlen

Quando ambos os terminais terminarem, envie a pasta `data/bronze/` para a
Kethlen no Slack — pode ser numa pasta do Google Drive ou enviando os CSVs
diretamente. Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` com as vagas
únicas para enriquecer. Esta máquina roda 4 terminais (e5–e8).

#### Passo 5 — Instalar o arquivo

Coloque o `vagas_unicas.csv` dentro de `data/silver/`.

```bash
cp ~/Downloads/vagas_unicas.csv data/silver/
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

Rode cada comando abaixo em um terminal separado. Quando o Chrome abrir,
confirme o login no Glassdoor e pressione Enter. Depois, encerre com Ctrl+C.

```bash
source venv/bin/activate
python3 enriquecer.py --inicio 30936 --fim 38670 --perfil chrome-profile-e5
# (outro terminal)
python3 enriquecer.py --inicio 38670 --fim 46404 --perfil chrome-profile-e6
# (outro terminal)
python3 enriquecer.py --inicio 46404 --fim 54138 --perfil chrome-profile-e7
# (outro terminal)
python3 enriquecer.py --inicio 54138 --fim 61872 --perfil chrome-profile-e8
```

#### Passo 7 — Rodar o enriquecimento (4 terminais tmux)

Abra 4 terminais (ou 4 janelas tmux) e rode um bloco em cada:

```bash
tmux new -s e5
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 30936 --fim 38670 \
  --perfil chrome-profile-e5 --assume-logged-in
# Ctrl+b d
```

```bash
tmux new -s e6
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 38670 --fim 46404 \
  --perfil chrome-profile-e6 --assume-logged-in
# Ctrl+b d
```

```bash
tmux new -s e7
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 46404 --fim 54138 \
  --perfil chrome-profile-e7 --assume-logged-in
# Ctrl+b d
```

```bash
tmux new -s e8
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 54138 --fim 61872 \
  --perfil chrome-profile-e8 --assume-logged-in
# Ctrl+b d
```

Para acompanhar o progresso: `tmux attach -t e5` (ou e6, e7, e8). Para desacoplar: `Ctrl+b d`.

#### Passo 8 — Enviar resultados para a Kethlen

Quando terminar, envie os arquivos `data/silver/enriquecido_*.csv` para a
Kethlen no Slack (Drive ou direto).

---

---

## Máquina 3 — PC Inteli (Marco)

Esta máquina roda a Fase 3 (enriquecimento) com 4 terminais (e9–e12) no Linux.

### Passo 0 — Setup (fazer uma vez)

```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

sudo apt install tmux    # se ainda não tiver
```

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv`. Esta máquina
roda 4 terminais (e9–e12).

#### Passo 1 — Instalar o arquivo

```bash
cp ~/Downloads/vagas_unicas.csv data/silver/
```

#### Passo 2 — Configurar perfis de enriquecimento (fazer uma vez)

Rode cada comando abaixo em um terminal separado. Quando o Chrome abrir,
confirme o login no Glassdoor e pressione Enter. Depois, encerre com Ctrl+C.

```bash
source venv/bin/activate
python3 enriquecer.py --inicio 61872 --fim 69606 --perfil chrome-profile-e9
# (outro terminal)
python3 enriquecer.py --inicio 69606 --fim 77339 --perfil chrome-profile-e10
# (outro terminal)
python3 enriquecer.py --inicio 77339 --fim 85072 --perfil chrome-profile-e11
# (outro terminal)
python3 enriquecer.py --inicio 85072 --fim 92805 --perfil chrome-profile-e12
```

#### Passo 3 — Rodar o enriquecimento (4 terminais tmux)

Abra 4 terminais (ou 4 janelas tmux) e rode um bloco em cada:

```bash
tmux new -s e9
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 61872 --fim 69606 \
  --perfil chrome-profile-e9 --assume-logged-in
# Ctrl+b d
```

```bash
tmux new -s e10
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 69606 --fim 77339 \
  --perfil chrome-profile-e10 --assume-logged-in
# Ctrl+b d
```

```bash
tmux new -s e11
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 77339 --fim 85072 \
  --perfil chrome-profile-e11 --assume-logged-in
# Ctrl+b d
```

```bash
tmux new -s e12
source venv/bin/activate
systemd-inhibit --what=sleep:idle python3 enriquecer.py \
  --inicio 85072 --fim 92805 \
  --perfil chrome-profile-e12 --assume-logged-in
# Ctrl+b d
```

Para acompanhar o progresso: `tmux attach -t e9` (ou e10, e11, e12). Para desacoplar: `Ctrl+b d`.

#### Passo 4 — Enviar resultados para a Kethlen

Quando terminar, envie os arquivos `data/silver/enriquecido_*.csv` para a
Kethlen no Slack (Drive ou direto).

---

---

## Máquina 4 — Leo

Esta máquina roda a Fase 3 (enriquecimento) com 4 terminais (e13–e16) no Windows.
Configure as Opções de Energia para nunca suspender antes de começar.

### Passo 0 — Setup (fazer uma vez)

```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv`. Esta máquina
roda 4 terminais (e13–e16).

#### Passo 1 — Instalar o arquivo

```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 2 — Configurar perfis de enriquecimento (fazer uma vez)

Abra 4 janelas do PowerShell e rode um comando em cada. Quando o Chrome abrir,
confirme o login no Glassdoor e pressione Enter. Depois, encerre com Ctrl+C.

```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 92805 --fim 100538 --perfil chrome-profile-e13
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 100538 --fim 108271 --perfil chrome-profile-e14
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 108271 --fim 116004 --perfil chrome-profile-e15
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 116004 --fim 123737 --perfil chrome-profile-e16
```

#### Passo 3 — Rodar o enriquecimento (4 PowerShells — manter abertos)

Abra 4 janelas do PowerShell e rode um bloco em cada. **Nao feche as janelas**
enquanto o processo estiver rodando.

```powershell
# PowerShell 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 92805 --fim 100538 --perfil chrome-profile-e13 --assume-logged-in
```

```powershell
# PowerShell 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 100538 --fim 108271 --perfil chrome-profile-e14 --assume-logged-in
```

```powershell
# PowerShell 3 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 108271 --fim 116004 --perfil chrome-profile-e15 --assume-logged-in
```

```powershell
# PowerShell 4 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio 116004 --fim 123737 --perfil chrome-profile-e16 --assume-logged-in
```

#### Passo 4 — Enviar resultados para a Kethlen

Quando terminar, envie os arquivos `data\silver\enriquecido_*.csv` para a
Kethlen no Slack (Drive ou direto).

---

---

## Referência rápida — tmux (macOS / Linux)

| Ação | Comando |
|------|---------|
| Criar sessão nomeada | `tmux new -s nome` |
| Desacoplar (processo continua) | `Ctrl+b d` |
| Reconectar | `tmux attach -t nome` |
| Listar sessões | `tmux ls` |
| Encerrar sessão | `tmux kill-session -t nome` |

---

## Resumo da distribuição — Fase 3

| Máquina | Pessoa | OS | e1 | e2 | e3 | e4 |
|---------|--------|----|----|----|----|----|
| M1 ⭐   | MacBook Kethlen | macOS | 0–7734 | 7734–15468 | 15468–23202 | 23202–30936 |
| M2      | PC Inteli Kethlen | Linux | 30936–38670 | 38670–46404 | 46404–54138 | 54138–61872 |
| M3      | PC Inteli Marco | Linux | 61872–69606 | 69606–77339 | 77339–85072 | 85072–92805 |
| M4      | Leo | Windows | 92805–100538 | 100538–108271 | 108271–116004 | 116004–123737 |

**Total de vagas únicas:** 123.737 — divididas em 16 terminais (4 máquinas × 4)
