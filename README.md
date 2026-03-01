<div align="center">
   <img src=".github/assets/logo.png" alt="Logo" width="300">
   <br>
   <h1>Sherlocky: AI-Powered Dark Web OSINT Tool</h1>

   <p>Sherlocky is an AI-powered tool for conducting dark web OSINT investigations. It leverages LLMs to refine queries, filter search results from dark web search engines, and provide an investigation summary.</p>
   <a href="#installation">Installation</a> &bull; <a href="#usage">Usage</a> &bull; <a href="#contributing">Contributing</a><br><br>
</div>

![Demo](.github/assets/screen-ui.png)


## Architecture
![Workflow](.github/assets/robin-workflow.png)

---

## Features

- ⚙️ **Modular Architecture** – Clean separation between search, scrape, and LLM workflows.
- 🤖 **Ollama-First LLM Support** – Uses Ollama by default and lets you choose any locally installed Ollama model.
- 🌐 **Web UI** – Streamlit-based interface for interactive investigations.
- 🐳 **Docker-Ready** – Recommended Docker deployment for clean, isolated usage.
- 📝 **Custom Reporting** – Save investigation output to file for reporting or further analysis.
- 🧩 **Extensible** – Easy to plug in new search engines or output formats.

---

## ⚠️ Disclaimer
> This tool is intended for educational and lawful investigative purposes only. Accessing or interacting with certain dark web content may be illegal depending on your jurisdiction. The maintainers are not responsible for any misuse of this tool or the data gathered using it.
>
> Use responsibly and at your own risk. Ensure you comply with all relevant laws and institutional policies before conducting OSINT investigations.
>
> Additionally, Sherlocky leverages local LLM inference via Ollama and third-party search sources. Be cautious when sending potentially sensitive queries.

## Installation
> [!NOTE]
> The tool needs Tor to do the searches. You can install Tor using `apt install tor` on Linux/Windows(WSL) or `brew install tor` on Mac. Once installed, confirm if Tor is running in the background.

> [!TIP]
> Sherlocky now uses **only Ollama** as LLM provider and the initial setup installs Ollama as a requirement.
>
> Run the bootstrap script for initial downloads/install:
> `bash setup.sh`
>
> Then confirm Ollama is running and that at least one model is installed (for example: `ollama pull llama3.2:latest`).
>
> If running in Docker, Ollama is already installed in the image and started automatically by the container entrypoint. For external Ollama setups, keep using `OLLAMA_BASE_URL` in `.env`.

### Docker [Recommended]

- Build the Docker image locally
```bash
docker build -t sherlocky:local .
```

- Run the docker image as:
```bash
docker run --rm \
   --name sherlocky \
   -v "$(pwd)/.env:/app/.env" \
   -v sherlocky-ollama:/root/.ollama \
   -p 8501:8501 \
   sherlocky:local
```

- Pull at least one model on first run:
```bash
docker exec -it sherlocky ollama pull llama3.2:latest
```

- Open your browser and navigate to `http://localhost:8501`

### Using Python (Development Version)

- With `Python 3.10+`, run initial setup and then start Streamlit:

```bash
bash setup.sh
streamlit run ui.py
```

- Open your browser and navigate to `http://localhost:8501`

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request if you have major feature updates.

- Fork the repository
- Create your feature branch (git checkout -b feature/amazing-feature)
- Commit your changes (git commit -m 'Add some amazing feature')
- Push to the branch (git push origin feature/amazing-feature)
- Open a Pull Request

Open an Issue for any of these situations:
- If you spot a bug or bad code
- If you have a feature request idea
- If you have questions or doubts about usage
- If you have minor code changes

---

