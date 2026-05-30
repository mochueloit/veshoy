import json
import secrets
import sys
from datetime import datetime
from pathlib import Path

TOKENS_FILE = Path(__file__).resolve().parent.parent / "data" / "tokens.json"


def load_tokens():
    if not TOKENS_FILE.exists():
        return {}
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tokens(tokens):
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=4, ensure_ascii=False)


def generate_token(email, role="user"):
    if role not in {"user", "admin"}:
        raise ValueError("El rol debe ser 'user' o 'admin'")

    tokens = load_tokens()
    new_token = secrets.token_hex(16)

    tokens[new_token] = {
        "email": email,
        "active": True,
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    save_tokens(tokens)
    print(f"\nToken generado para: {email}")
    print(f"Rol: {role}")
    print(f"Token: {new_token}")
    print("Usar en el header: x-token\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python manage_tokens.py usuario@correo.com [user|admin]")
    else:
        email = sys.argv[1]
        role = sys.argv[2] if len(sys.argv) > 2 else "user"
        generate_token(email, role)
