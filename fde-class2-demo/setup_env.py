"""Write local Ollama model settings to this project's .env file."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
from app import DEFAULT_MODEL


def quote(value):
    if "\n" in value or "\r" in value:
        raise ValueError("Settings must be single-line values")
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main():
    model = input(f"Local Ollama model [{DEFAULT_MODEL}]: ").strip() or DEFAULT_MODEL
    path = BASE_DIR / ".env"
    try:
        if "cloud" in model.lower():
            raise ValueError("A local model is required")
        content = f"APP_OLLAMA_MODEL={quote(model)}\n"
        # Restrict permissions before writing, including when replacing existing content.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.truncate(0)
            stream.write(content)
    except (OSError, ValueError):
        print("Could not write project configuration.")
        return
    print("Project .env written for local Ollama. No API key is needed.")


if __name__ == "__main__":
    main()
