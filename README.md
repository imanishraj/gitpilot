# ✈ GitPilot

> Your AI-powered git wizard — push, branch, pull, clone, and manage GitHub repos with a single command. No git knowledge required.

GitPilot combines the power of **Git**, **GitHub API**, and **Ollama** (a free, fully offline AI engine) to automate your entire GitHub workflow. It reads your project code, writes a professional README, generates smart commit messages, creates your repo, and pushes — all from one interactive menu.

---

## Why Ollama?

GitPilot uses **[Ollama](https://ollama.com)** to run AI models **100% locally on your machine** — no API keys, no subscriptions, no internet required for AI features.

> Ollama is a powerful open-source tool that lets you run large language models like Granite, LLaMA, Mistral, and Qwen right on your laptop. It is completely free and works offline, making it ideal for developers who want AI assistance without depending on paid cloud services.

- Download Ollama: **https://ollama.com/download**
- Browse available models: **https://ollama.com/library**
- Recommended model for GitPilot: **[granite3.3:8b](https://ollama.com/library/granite3.3)**

```bash
# Install the recommended model
ollama pull granite3.3:8b

# Start Ollama before using GitPilot
ollama serve
```

> GitPilot works even when Ollama is offline — it just skips AI features and asks you to type your commit message manually.

---

## Features

- **One command** — interactive menu guides you through everything
- **Auto README** — reads your code and generates a professional README using Ollama
- **Smart commit messages** — AI reads your `git diff` and writes the commit message for you
- **Repo management** — checks if your repo exists on GitHub, creates it if not
- **Branch workflow** — create, switch, and push branches easily
- **Pull support** — pull latest changes from any branch
- **Clone repos** — browse your own GitHub repos or paste any URL to clone directly to your laptop, then open in Cursor or VS Code automatically
- **Error diagnosis** — when a git command fails, Ollama reads the error and tells you exactly how to fix it
- **Secure credentials** — your GitHub token is stored locally in `~/.gitpilot_config.json`, never inside your project
- **Media file protection** — automatically ignores `.wav`, `.mp3`, `.mp4`, and other large files

---

## Installation

### Option 1 — Install via pip (recommended)

```bash
pip install gitpilot
```

### Option 2 — Install from source

```bash
git clone https://github.com/J-joke-r/gitpilot.git
cd gitpilot
pip install .
```

### Option 3 — Run directly without installing

```bash
pip install requests
python gitpilot/cli.py
```

---

## Requirements

- Python 3.10 or above
- Git installed on your system
- A GitHub account with a [Personal Access Token](https://github.com/settings/tokens) (classic, `repo` scope)
- Ollama installed for AI features (optional but recommended)

---

## Usage

Navigate to any project folder and run:

```bash
cd your-project
gitpilot
```

You will see:

```
╔══════════════════════════════════════════╗
║     GitPilot — your AI git wizard  ✈    ║
╚══════════════════════════════════════════╝
  Project : your-project
  GitHub  : your-username
  Ollama  : running ✓

  What do you want to do?

  1.  Push project to GitHub  (new or existing repo)
  2.  Create a new branch
  3.  Pull latest from GitHub
  4.  Switch branch
  5.  Project status
  6.  Clone a repo to your laptop
  7.  Reset GitHub credentials
  0.  Exit
```

### Clone a repo

Option 6 lets you clone in two ways:

```
  Clone options:

  1. From your own GitHub repos   ← shows a numbered list of all your repos
  2. From any GitHub URL          ← paste any public or private repo URL
```

After cloning, GitPilot asks if you want to open the project in Cursor or VS Code automatically.

### First run

On first launch, GitPilot asks for your GitHub credentials once and saves them securely:

```
  Paste GitHub token: ghp_xxx...
  GitHub username   : your-username

  Credentials saved!
```

### Reset credentials

```bash
gitpilot --reset
```

Or choose option 7 from the menu.

---

## How it works

```
You run gitpilot
       │
       ├── Reads your project code
       │
       ├── Sends code to Ollama (local AI) → generates README
       │
       ├── Checks GitHub API → repo exists? create if not
       │
       ├── git init → git add → Ollama reads diff → commit message
       │
       └── git push → prints live GitHub URL
```

---

## Folder Structure

```
gitpilot/
├── gitpilot/
│   ├── __init__.py      # version info
│   ├── cli.py           # entry point and menu
│   └── core.py          # all logic — git, GitHub API, Ollama
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## Getting a GitHub Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Give it a name like `gitpilot`
4. Check the **`repo`** scope
5. Click **Generate token** and copy it immediately
6. Paste it when GitPilot asks on first run

---

## Recommended Ollama Models

| Model | Size | Best for |
|---|---|---|
| `granite3.3:8b` | ~5GB | README writing, commit messages (recommended) |
| `qwen2.5-coder:7b` | ~4.7GB | Code-heavy projects |
| `tinyllama` | ~1.5GB | Low RAM systems |

```bash
ollama pull granite3.3:8b
ollama serve
```

---

## License

MIT — free to use, modify, and distribute.

---

## Author

Built by [J-joke-r](https://github.com/J-joke-r) — a fun side project to make GitHub workflows effortless for every developer.
