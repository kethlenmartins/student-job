#!/usr/bin/env bash
# Abre o Chrome com remote debugging em um diretório DEDICADO (.chrome-debug).
# O Chrome não permite remote debugging no perfil padrão do sistema.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

carregar_env() {
  while IFS= read -r linha || [[ -n "$linha" ]]; do
    [[ -z "$linha" || "$linha" =~ ^[[:space:]]*# ]] && continue
    if [[ "$linha" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      chave="${BASH_REMATCH[1]}"
      valor="${BASH_REMATCH[2]}"
      valor="${valor#\"}" ; valor="${valor%\"}"
      valor="${valor#\'}" ; valor="${valor%\'}"
      export "$chave=$valor"
    fi
  done < .env
}

if [[ -f .env ]]; then
  carregar_env
fi

PORTA="${CHROME_DEBUG_PORT:-9222}"
PERFIL="${CHROME_PROFILE_DIRECTORY:-Default}"
USER_DATA="${CHROME_USER_DATA_DIR:-$SCRIPT_DIR/.chrome-debug}"

if [[ "$USER_DATA" != /* ]]; then
  USER_DATA="$SCRIPT_DIR/$USER_DATA"
fi

CHROME_SISTEMA="$HOME/Library/Application Support/Google/Chrome"
if [[ "$USER_DATA" == "$CHROME_SISTEMA" ]]; then
  echo "ERRO: não use o diretório padrão do Chrome do sistema."
  echo "O remote debugging exige um diretório dedicado."
  echo ""
  echo "Use no .env:"
  echo "  CHROME_USER_DATA_DIR=$SCRIPT_DIR/.chrome-debug"
  echo "  CHROME_PROFILE_DIRECTORY=Default"
  exit 1
fi

mkdir -p "$USER_DATA"

echo "Fechando Chrome existente..."
osascript -e 'quit app "Google Chrome"' 2>/dev/null || true
pkill -f "remote-debugging-port=${PORTA}" 2>/dev/null || true
sleep 2

echo "Abrindo Chrome dedicado à coleta..."
echo "  User Data: $USER_DATA"
echo "  Perfil:    $PERFIL"
echo "  Porta:     $PORTA"
echo ""

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port="$PORTA" \
  --remote-allow-origins=* \
  --user-data-dir="$USER_DATA" \
  --profile-directory="$PERFIL" &

echo "Aguardando porta de debug..."
for _ in $(seq 1 20); do
  if curl -s "http://127.0.0.1:${PORTA}/json/version" | grep -q Browser; then
    echo ""
    echo "Chrome pronto na porta $PORTA."
    echo ""
    echo "Na PRIMEIRA vez, faça login no Glassdoor:"
    echo "  1. Acesse https://www.glassdoor.com.br"
    echo "  2. Entrar → Continuar com Google"
    echo "  3. Conclua o login Firebase"
    echo ""
    echo "Depois, em outro terminal:"
    echo "  python coleta_glassdoor.py"
    exit 0
  fi
  sleep 1
done

echo ""
echo "ERRO: a porta $PORTA não respondeu."
echo "Verifique se o Chrome abriu e se nenhum outro processo usa essa porta."
