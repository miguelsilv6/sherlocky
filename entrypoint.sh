#!/bin/bash
set -e

echo "Starting Tor..."
tor &

echo "Waiting for Tor to be ready (127.0.0.1:9050)..."

# Loop until port 9050 is open, timeout after 60 seconds
if ! timeout 60 bash -c '
until python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect((\"127.0.0.1\", 9050)); s.close()" 2>/dev/null; do
  echo "Waiting for Tor socket..."
  sleep 2
done
'
then
  echo "ERROR: Tor failed to start or is not listening on port 9050."
  exit 1
fi

echo "Tor is ready."

echo "Starting Ollama..."
ollama serve >/tmp/ollama.log 2>&1 &

echo "Waiting for Ollama to be ready (127.0.0.1:11434)..."
if ! timeout 60 bash -c '
until python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect((\"127.0.0.1\", 11434)); s.close()" 2>/dev/null; do
  echo "Waiting for Ollama socket..."
  sleep 2
done
'
then
  echo "ERROR: Ollama failed to start or is not listening on port 11434."
  echo "Last Ollama logs:"
  tail -n 50 /tmp/ollama.log || true
  exit 1
fi

echo "Ollama is ready."
echo "Starting Sherlocky: AI-Powered Dark Web OSINT Tool..."
exec streamlit run ui.py --server.port=8501 --server.address=0.0.0.0
