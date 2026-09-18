from pathlib import Path



text = "\n#migrate from logging with print and standard logging module to loguru\n"
for py_file in Path.cwd().glob("*.py"):
    try:
        py_file.write_text(py_file.read_text(encoding="utf-8") + text, encoding="utf-8")
        print(f"✓ Updated: {py_file.name}")
    except Exception as e:
        print(f"✗ Error: {py_file.name} - {e}")
