from pathlib import Path
from watchfiles import watch
if __name__ == "__main__":
    cwd = Path.cwd().resolve()
    print(f"watching {cwd} for changes ...")
    for change in watch(str(cwd)):
        print(change)
