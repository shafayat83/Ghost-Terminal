# 👻 Ghost Terminal

**Elite AI Systems Architect** — An OS-level AI entity that translates natural language into dynamically generated, locally executed scripts.

---

## 🌑 The Concept
Ghost Terminal is designed to be your system's "ghost in the machine." It bridges the gap between human intent and machine execution by using a local **Ollama** LLM to generate precise, environment-aware code on the fly.

> [!IMPORTANT]
> **Safety First**: Ghost Terminal never executes code without your explicit consent. It includes a built-in confirmation loop and detects potentially destructive actions (like file deletion) to request double-confirmation.

---

## 🛠️ Core Architecture
Ghost Terminal follows a streamlined, robust workflow:

1. **The Listener**: Captures natural language input from the terminal.
2. **The Translator**: Consults a local Ollama API (Llama3, CodeLlama, etc.) with a constrained system prompt.
3. **The Generator**: Extracts raw, executable code (Python, Bash, or PowerShell) while stripping all markdown.
4. **The Executor**: Saves the code to a temporary file, runs it via `subprocess`, and captures real-time output.
5. **The Cleaner**: Automatically wipes temporary scripts after execution to maintain a clean filesystem.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: Download from [ollama.com](https://ollama.com).
- **A Code-Capable Model**: We recommend `llama3` or `codellama`.
  ```bash
  ollama pull llama3
  ```

### 2. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Usage
Run Ghost Terminal in **Interactive Mode**:
```bash
python ghost.py
```

Or pass a **Single Command**:
```bash
python ghost.py "Find all log files larger than 10MB and compress them into a zip"
```

---

## 🛡️ Safety & Constraints
Ghost Terminal is built with several hard constraints to protect your system:

- **Zero Markdown**: The orchestrator strictly filters LLM output to ensure only executable code reaches the shell.
- **Environment Awareness**: Automatically detects if you are running on **Windows Native** or **WSL** (Windows Subsystem for Linux) and adjusts paths and commands accordingly.
- **Confirmation Loop**: Prints the generated script to your console and waits for a `Y/N` confirmation.
- **Destructive Action Protection**: Specifically monitors for keywords like `rm`, `del`, and `rmtree`, requiring an extra confirmation layer for these tasks.

---

## 📂 Project Structure
```text
Ghost Terminal/
├── ghost.py           # The complete orchestrator (Listener, Translator, Executor)
├── requirements.txt   # Necessary dependencies (requests, send2trash)
├── .gitignore         # Keeps your repo clean
└── LICENSE            # MIT License
```

---

## 📜 License
This project is licensed under the **MIT License**. Use it at your own risk. Ghost Terminal executes AI-generated code; always review the proposed script before confirming execution.

---

*Designed for the elite developer who wants to move at the speed of thought.*
