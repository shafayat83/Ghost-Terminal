"""
Ghost Terminal Configuration
============================
Central configuration for all Ghost Terminal settings.
Modify these values to customize behavior.
"""

# Ollama API Settings
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_MODEL = "llama3"  # Recommended: llama3, dolphin-mixtral, or codellama

# Script Generation Settings
TEMP_SCRIPTS_DIR = "scripts"  # Relative to project root
PYTHON_SCRIPT_NAME = "temp_ghost_script.py"
BASH_SCRIPT_NAME = "temp_ghost_script.bat"  # Windows
WSL_SCRIPT_NAME = "temp_ghost_script.sh"   # WSL/Linux

# Safety Settings
REQUIRE_CONFIRMATION = True  # Always ask before executing generated code
DESTRUCTIVE_ACTION_KEYWORDS = [
    "delete", "remove", "rm", "del", "rmdir", 
    "shutil.rmtree", "os.remove", "os.unlink",
    "format", "destroy", "erase"
]
DOUBLE_CONFIRM_DESTRUCTIVE = True  # Require double confirmation for destructive actions

# Code Generation Settings
MAX_CODE_LENGTH = 50000  # Maximum characters in generated code
EXECUTION_TIMEOUT = 300  # Maximum execution time in seconds (5 minutes)

# System Prompt Template
# This is the CRITICAL prompt that instructs the LLM how to generate code
SYSTEM_PROMPT = """You are a Code Generation Engine for Ghost Terminal.
Your ONLY job is to output raw, executable code. NO explanations. NO markdown. NO comments about what you're doing.

RULES:
1. Output ONLY the code itself - no ```python or ```bash wrappers
2. No explanatory text before or after the code
3. Use Python 3.10+ syntax for Python scripts
4. For Windows: use PowerShell-compatible commands or .bat syntax
5. For file deletion: NEVER use shutil.rmtree or os.remove directly - instead use send2trash or print a warning
6. Always include error handling (try/except blocks)
7. Print meaningful output to stdout so the user sees results
8. If the task cannot be safely accomplished, print an error message and exit(1)

DESTRUCTIVE ACTION PROTOCOL:
If the request involves deleting files:
- Use send2trash library if available
- OR use PowerShell's Remove-Item with -Confirm for .bat scripts
- NEVER silently delete files without any confirmation mechanism

OUTPUT FORMAT:
- Just the raw code, nothing else
- I will repeat: NO markdown, NO explanations, JUST CODE

Example correct output:
import os
print(os.listdir('.'))

Example WRONG output (never do this):
```python
# Here's the code to list files
import os
print(os.listdir('.'))
```

Generate the code for this request:
"""
