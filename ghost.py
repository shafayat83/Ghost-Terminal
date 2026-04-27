"""
Ghost Terminal - OS-Level AI Entity
==================================
An Elite AI Systems Architect tool that translates natural language commands 
into dynamically generated, locally executed scripts.

ARCHITECTURE:
1. The Listener    - Captures natural language intent from the user.
2. The Translator  - Consults a local Ollama API with a constrained system prompt.
3. The Generator   - Extracts raw executable code (Python/Shell/PowerShell).
4. The Executor    - Runs code via subprocess after explicit user confirmation.
5. The Cleaner     - Securely wipes temporary script files after execution.

Author: Ghost Terminal Project
License: MIT
"""

import os
import sys
import re
import subprocess
import requests
import platform
import tempfile
from pathlib import Path

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  # Change to your preferred local model
TEMP_FILENAME = "temp_ghost_script"

# Attempt to import send2trash for safe deletion
try:
    import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False

class GhostTerminal:
    """
    The main orchestrator for Ghost Terminal.
    Handles the loop of: Listen -> Translate -> Confirm -> Execute -> Clean.
    """
    
    def __init__(self, model=OLLAMA_MODEL):
        self.model = model
        self.os_type = self._detect_environment()
        self.system_prompt = self._build_system_prompt()

    def _detect_environment(self):
        """Constraint 4: Detect environment for path and shell awareness."""
        is_windows = platform.system() == "Windows"
        is_wsl = "microsoft-standard" in platform.release().lower()
        
        if is_wsl:
            return "WSL"
        elif is_windows:
            return "WINDOWS"
        return "LINUX"

    def _build_system_prompt(self):
        """Constraint 3: Safe instructions and strict output formatting."""
        return f"""You are 'Ghost Terminal', an Elite AI Systems Architect.
Your task is to translate natural language into raw, executable code for {self.os_type}.

STRICT CONSTRAINTS:
1. Output ONLY raw code. NO markdown (no ```), NO explanations, NO intro text.
2. If the user implies deleting files (rm, del, rmtree), ALWAYS use safe deletion methods.
   - For Python: use 'send2trash.send2trash(path)' if possible.
   - For Shell: use 'mv path ~/.local/share/Trash/' or similar safe methods.
3. Ensure paths are correct for {self.os_type}.
4. Default to Python for complex logic, or PowerShell/Bash for simple OS tasks.
"""

    def strip_markdown(self, text):
        """Constraint 1: Regex to strip any markdown formatting from LLM output."""
        # Remove triple backtick blocks
        text = re.sub(r'```[a-zA-Z]*\n?', '', text)
        text = text.replace('```', '')
        return text.strip()

    def translate_request(self, user_input):
        """The Translator: Communicates with local Ollama API."""
        payload = {
            "model": self.model,
            "prompt": f"{self.system_prompt}\nUser Request: {user_input}\nCode:",
            "stream": False,
            "options": {
                "temperature": 0.1  # Keep it deterministic
            }
        }
        
        try:
            print(f"\n[Ghost] Translating request via {self.model}...")
            response = requests.post(OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            raw_output = response.json().get("response", "")
            return self.strip_markdown(raw_output)
        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to Ollama. Is it running? (ollama serve)")
            return None
        except Exception as e:
            print(f"ERROR: {e}")
            return None

    def execute_script(self, code):
        """The Executor: Confirmation loop, subprocess execution, and results capture."""
        if not code:
            print("[Ghost] Failed to generate code.")
            return

        # Determine language/shell
        is_python = "import " in code or "print(" in code or "sys." in code
        suffix = ".py" if is_python else (".ps1" if self.os_type == "WINDOWS" else ".sh")
        
        print("\n" + "═"*50)
        print(" GENERATED CODE ".center(50, "═"))
        print(code)
        print("═"*50)
        
        # Constraint 2: Confirmation Loop
        print(f"\nTarget Environment: {self.os_type}")
        choice = input("Execute this script? (Y/N): ").strip().lower()
        
        if choice != 'y':
            print("[Ghost] Execution cancelled.")
            return

        # Double Confirmation for Destructive Actions (Constraint 3)
        destructive = any(kw in code.lower() for kw in ['rm ', 'del ', 'rmtree', 'remove', 'unlink'])
        if destructive:
            choice = input("!! DESTRUCTIVE ACTION DETECTED !! Double confirm execution? (Y/N): ").strip().lower()
            if choice != 'y':
                print("[Ghost] Safety abort.")
                return

        # Save to temporary file
        temp_dir = Path(tempfile.gettempdir())
        script_path = temp_dir / f"{TEMP_FILENAME}{suffix}"
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            # Prepare execution command based on language and environment
            if is_python:
                cmd = [sys.executable, str(script_path)]
            elif self.os_type == "WINDOWS":
                # Ensure we use PowerShell on Windows
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
            else:
                # Ensure execution permissions on Unix-like systems
                os.chmod(script_path, 0o755)
                cmd = ["bash", str(script_path)]

            print(f"\n[Ghost] Executing...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Print results back to user
            if result.stdout:
                print(f"\n--- STDOUT ---\n{result.stdout}")
            if result.stderr:
                print(f"\n--- STDERR ---\n{result.stderr}")
            
            if result.returncode == 0:
                print("\n[Ghost] Execution successful.")
            else:
                print(f"\n[Ghost] Execution failed with return code {result.returncode}")

        except Exception as e:
            print(f"\n[Ghost] Runtime error: {e}")
        finally:
            # The Cleaner: Delete temporary file
            if script_path.exists():
                os.remove(script_path)
                print("[Ghost] Temporary script deleted.")

    def run_listener(self):
        """The Listener: Main interactive loop."""
        print(f"\nGhost Terminal Online | Env: {self.os_type} | Model: {self.model}")
        print("Type your request in natural language (e.g., 'list all pdfs here'). Type 'exit' to quit.")
        
        while True:
            try:
                user_input = input("\nGhost $> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("[Ghost] Ghost Terminal offline.")
                    break
                
                code = self.translate_request(user_input)
                self.execute_script(code)
                
            except KeyboardInterrupt:
                print("\n[Ghost] Interrupted. Goodbye.")
                break

if __name__ == "__main__":
    # Check if a single command was passed as an argument
    terminal = GhostTerminal()
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        generated_code = terminal.translate_request(command)
        terminal.execute_script(generated_code)
    else:
        # Otherwise, enter interactive listener mode
        terminal.run_listener()
