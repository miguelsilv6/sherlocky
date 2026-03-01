#!/usr/bin/env bash
set -euo pipefail

echo "Starting Sherlocky initial setup..."

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_ollama() {
  if command_exists ollama; then
    echo "Ollama already installed."
    return
  fi

  os="$(uname -s)"
  case "$os" in
    Darwin)
      if ! command_exists brew; then
        echo "Homebrew is required on macOS to install Ollama automatically."
        echo "Install Homebrew first: https://brew.sh/"
        exit 1
      fi
      echo "Installing Ollama with Homebrew..."
      brew install ollama
      ;;
    Linux)
      echo "Installing Ollama using official installer..."
      curl -fsSL https://ollama.com/install.sh | sh
      ;;
    *)
      echo "Unsupported OS: $os"
      echo "Install Ollama manually: https://ollama.com/download"
      exit 1
      ;;
  esac
}

install_tor() {
  if command_exists tor; then
    echo "Tor already installed."
    return
  fi

  os="$(uname -s)"
  case "$os" in
    Darwin)
      if ! command_exists brew; then
        echo "Homebrew is required on macOS to install Tor automatically."
        echo "Install Homebrew first: https://brew.sh/"
        exit 1
      fi
      echo "Installing Tor with Homebrew..."
      brew install tor
      ;;
    Linux)
      if command_exists apt-get; then
        echo "Installing Tor with apt..."
        sudo apt-get update
        sudo apt-get install -y tor
      else
        echo "Automatic Tor install is supported only for apt-based Linux distros."
        echo "Install Tor manually before running Sherlocky."
        exit 1
      fi
      ;;
    *)
      echo "Unsupported OS: $os"
      echo "Install Tor manually before running Sherlocky."
      exit 1
      ;;
  esac
}

echo "Installing system dependencies (Tor + Ollama)..."
install_tor
install_ollama

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Setup complete."
echo "Next:"
echo "1) Start Ollama service if needed: ollama serve"
echo "2) Pull at least one model: ollama pull llama3.2:latest"
echo "3) Launch app: streamlit run ui.py"
