import subprocess
import os
import pytest

def test_ui_interactions_and_regression_suite():
    """
    Executes the comprehensive automated UI regression test suite:
    - Sidebar open / close / toggle / focus auto-collapse
    - Floating continual button at bottom-center with hover reveal
    - Textbox plus button and menu actions
    - Enter and Ctrl+Enter submission
    - Shift+Enter multiline newline
    - Continual learning submission routing
    - IME composition suppression
    - Zero placeholder attributes
    - Zero JavaScript errors
    """
    script_path = os.path.join(os.path.dirname(__file__), "test_ui_regression.js")
    proc = subprocess.run(["node", script_path], capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    assert proc.returncode == 0, f"UI regression test failed: {proc.stdout}\n{proc.stderr}"
