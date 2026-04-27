"""
Safety Checker Module
=====================
Implements safety protocols for dynamically generated code execution.

CRITICAL SECURITY FEATURES:
1. Detects destructive operations (file deletion, system modifications)
2. Implements confirmation loops before execution
3. Provides double-confirmation for high-risk operations
4. Analyzes code for potentially dangerous patterns

WHY THIS MATTERS:
- Prevents accidental data loss from AI-generated code
- Gives users full visibility into what will execute
- Implements defense-in-depth against malicious or buggy code generation
"""

import re
from typing import List, Tuple, Optional
from pathlib import Path


class SafetyChecker:
    """
    Analyzes code for potentially dangerous operations.
    
    This class implements multiple layers of safety:
    1. Pattern matching for dangerous keywords
    2. Context analysis (what is the code trying to do?)
    3. Risk scoring (how dangerous is this operation?)
    4. User confirmation enforcement
    """
    
    # Destructive action patterns with risk levels (1-5, 5 = most dangerous)
    DESTRUCTIVE_PATTERNS = {
        # File deletion - HIGH RISK
        'shutil.rmtree': ('Delete directory tree', 5),
        'os.remove': ('Delete file', 4),
        'os.unlink': ('Delete file (unlink)', 4),
        'os.rmdir': ('Remove directory', 4),
        'Path.unlink': ('Delete file (Path)', 4),
        'Path.rmdir': ('Remove directory (Path)', 4),
        'rm -rf': ('Force delete (Unix)', 5),
        'Remove-Item -Recurse -Force': ('Force delete (PowerShell)', 5),
        'del /F': ('Force delete (CMD)', 4),
        'del /Q': ('Quiet delete (CMD)', 4),
        
        # System modifications - HIGH RISK
        'subprocess.call': ('Execute system command', 3),
        'subprocess.run': ('Execute system command', 3),
        'os.system': ('Execute shell command', 4),
        'eval(': ('Evaluate dynamic code', 5),
        'exec(': ('Execute dynamic code', 5),
        '__import__': ('Dynamic import', 4),
        
        # Network operations - MEDIUM RISK
        'requests.post': ('HTTP POST request', 3),
        'socket.': ('Network socket operation', 3),
        'urllib.request': ('URL request', 2),
        
        # File system - MEDIUM RISK
        'shutil.move': ('Move/rename file', 2),
        'shutil.copy': ('Copy file', 1),
        'os.rename': ('Rename file', 2),
        'os.makedirs': ('Create directory', 1),
        'Path.write_text': ('Write to file', 2),
        'open(..., "w")': ('Write to file', 2),
        'open(..., "a")': ('Append to file', 2),
        
        # Environment - MEDIUM RISK
        'os.environ': ('Environment variable access', 3),
        'os.setenv': ('Set environment variable', 4),
        'os.putenv': ('Set environment variable', 4),
    }
    
    # Safe deletion alternatives to suggest
    SAFE_DELETION_SUGGESTIONS = {
        'send2trash': 'Sends files to trash/recycle bin (recoverable)',
        'PowerShell Remove-Item -Confirm': 'Prompts before deletion',
        'shutil.move to backup': 'Move to backup instead of delete',
    }
    
    def __init__(self, require_confirmation: bool = True, 
                 double_confirm_destructive: bool = True):
        """
        Initialize the SafetyChecker.
        
        Args:
            require_confirmation: Always ask for Y/N before execution
            double_confirm_destructive: Require double confirmation for high-risk code
        """
        self.require_confirmation = require_confirmation
        self.double_confirm_destructive = double_confirm_destructive
        self.detected_patterns = []
        self.risk_score = 0
        self.is_destructive = False
    
    def analyze(self, code: str, script_type: str = 'python') -> dict:
        """
        Analyze code for dangerous patterns.
        
        This method scans the code for all known dangerous patterns
        and calculates an overall risk score.
        
        Args:
            code: Code to analyze
            script_type: Type of script ('python', 'bash', 'powershell')
            
        Returns:
            dict: Analysis results including:
                - risk_score: 0-10 score (higher = more dangerous)
                - is_destructive: Boolean for destructive operations
                - detected_patterns: List of found patterns
                - requires_double_confirm: Boolean for extra confirmation
        """
        self.detected_patterns = []
        self.risk_score = 0
        self.is_destructive = False
        
        # Scan for each dangerous pattern
        for pattern, (description, base_risk) in self.DESTRUCTIVE_PATTERNS.items():
            if self._pattern_in_code(pattern, code, script_type):
                self.detected_patterns.append({
                    'pattern': pattern,
                    'description': description,
                    'base_risk': base_risk,
                })
                self.risk_score += base_risk
                
                # Mark as destructive if high-risk pattern found
                if base_risk >= 4:
                    self.is_destructive = True
        
        # Cap risk score at 10
        self.risk_score = min(self.risk_score, 10)
        
        # Determine if double confirmation is needed
        requires_double_confirm = (
            self.double_confirm_destructive and 
            self.is_destructive and 
            self.risk_score >= 5
        )
        
        return {
            'risk_score': self.risk_score,
            'is_destructive': self.is_destructive,
            'detected_patterns': self.detected_patterns,
            'requires_double_confirm': requires_double_confirm,
            'safe_to_execute': self.risk_score < 3,
        }
    
    def _pattern_in_code(self, pattern: str, code: str, script_type: str) -> bool:
        """
        Check if a pattern exists in the code.
        
        Handles both literal string matching and regex patterns.
        
        Args:
            pattern: Pattern to search for
            code: Code to search in
            script_type: Type of script (for context-aware matching)
            
        Returns:
            bool: True if pattern found
        """
        # Handle regex patterns (containing special chars)
        if any(char in pattern for char in '.*+?^${}()|[]\\'):
            try:
                return bool(re.search(pattern, code))
            except re.error:
                return False
        
        # Simple string matching
        return pattern in code
    
    def get_risk_summary(self) -> str:
        """
        Generate a human-readable risk summary.
        
        Returns:
            str: Formatted risk summary for display to user
        """
        if not self.detected_patterns:
            return "[OK] No dangerous patterns detected"
        
        lines = ["[WARN] POTENTIALLY DANGEROUS OPERATIONS DETECTED:", ""]
        
        for i, pattern_info in enumerate(self.detected_patterns, 1):
            lines.append(
                f"  {i}. {pattern_info['description']} "
                f"(pattern: '{pattern_info['pattern']}')"
            )
        
        lines.append("")
        lines.append(f"  Overall Risk Score: {self.risk_score}/10")
        
        if self.is_destructive:
            lines.append("  [CRITICAL] DESTRUCTIVE OPERATION - Extra caution advised")
        
        return '\n'.join(lines)
    
    def get_safe_alternatives(self) -> List[str]:
        """
        Get suggestions for safer alternatives to detected patterns.
        
        Returns:
            list: List of safer alternative suggestions
        """
        suggestions = []
        
        for pattern_info in self.detected_patterns:
            pattern = pattern_info['pattern']
            
            # Check for deletion patterns
            if any(del_pattern in pattern for del_pattern in 
                   ['remove', 'unlink', 'rmdir', 'rmtree', 'rm ']):
                for safe_method, description in self.SAFE_DELETION_SUGGESTIONS.items():
                    suggestions.append(f"  • Use '{safe_method}' - {description}")
        
        return suggestions
    
    def confirm_execution(self, code: str, script_type: str = 'python', 
                         double_confirm: bool = False) -> bool:
        """
        Present code to user and request confirmation.
        
        This is the CRITICAL safety gate - no code executes without
        passing through this confirmation loop.
        
        Args:
            code: Code to be executed
            script_type: Type of script
            double_confirm: Require double confirmation (Y twice)
            
        Returns:
            bool: True if user confirms, False otherwise
        """
        print("\n" + "=" * 70)
        print("[GHOST TERMINAL] EXECUTION CONFIRMATION")
        print("=" * 70)
        
        # Show risk analysis
        analysis = self.analyze(code, script_type)
        print(self.get_risk_summary())
        
        # Show safe alternatives if destructive
        if self.is_destructive:
            print("\n[HINT] SAFER ALTERNATIVES:")
            for suggestion in self.get_safe_alternatives():
                print(suggestion)
        
        # Display the code
        print("\n" + "-" * 70)
        print("CODE TO EXECUTE:")
        print("-" * 70)
        
        # Show code with line numbers
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:4d} | {line}")
        
        print("-" * 70)
        print(f"Script Type: {script_type.upper()}")
        print(f"Risk Level: {self.risk_score}/10 ({'HIGH' if self.risk_score >= 5 else 'MEDIUM' if self.risk_score >= 3 else 'LOW'})")
        print()
        
        # First confirmation
        confirm_prompt = "Execute this script? (Y/N): "
        if double_confirm:
            confirm_prompt = "[CRITICAL] DESTRUCTIVE OPERATION - Execute anyway? (Y/N): "
        
        response = input(confirm_prompt).strip().lower()
        
        if response not in ['y', 'yes']:
            print("\n❌ Execution cancelled by user")
            return False
        
        # Double confirmation for destructive operations
        if double_confirm:
            print("\n[CRITICAL] DOUBLE CONFIRMATION REQUIRED")
            print("Type 'DELETE' to confirm destructive operation:")
            double_response = input("> ").strip()
            
            if double_response.upper() != 'DELETE':
                print("\n[CANCEL] Execution cancelled - double confirmation failed")
                return False
            
            print("\n[OK] Double confirmation received")
        
        print("\n[OK] Execution confirmed")
        return True
    
    def confirm_safe_deletion(self, file_path: str) -> bool:
        """
        Special confirmation for file deletion operations.
        
        Provides additional context about what will be deleted.
        
        Args:
            file_path: Path to file/directory that will be deleted
            
        Returns:
            bool: True if user confirms deletion
        """
        print("\n" + "=" * 70)
        print("[FILE DELETION] CONFIRMATION")
        print("=" * 70)
        
        # Check if path exists
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
                print(f"  File: {file_path}")
                print(f"  Size: {size:,} bytes")
            elif path.is_dir():
                file_count = sum(1 for _ in path.rglob('*'))
                print(f"  Directory: {file_path}")
                print(f"  Contains: {file_count} items")
        else:
            print(f"  ⚠️  Path does not exist: {file_path}")
        
        print("\n⚠️  This operation may be IRREVERSIBLE")
        print("\nRecommended: Use send2trash for recoverable deletion")
        print()
        
        response = input("Proceed with deletion? (Y/N): ").strip().lower()
        return response in ['y', 'yes']


# Convenience function
def check_and_confirm(code: str, script_type: str = 'python', 
                     require_double: bool = False) -> Tuple[bool, dict]:
    """
    Quick safety check and confirmation.
    
    Args:
        code: Code to check
        script_type: Type of script
        require_double: Require double confirmation
        
    Returns:
        Tuple of (confirmed: bool, analysis: dict)
    """
    checker = SafetyChecker()
    analysis = checker.analyze(code, script_type)
    
    if require_double or analysis['requires_double_confirm']:
        confirmed = checker.confirm_execution(code, script_type, double_confirm=True)
    else:
        confirmed = checker.confirm_execution(code, script_type)
    
    return confirmed, analysis
