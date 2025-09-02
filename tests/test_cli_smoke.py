import subprocess, sys

def test_cli_help():
    r = subprocess.run([sys.executable, "-m", "statline.cli", "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "StatLine Core CLI" in r.stdout
