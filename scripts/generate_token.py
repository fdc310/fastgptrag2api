"""Generate an AES-256-CBC auth token for the FastGPT RAG API.

Usage:
    python scripts/generate_token.py <device_name> [--key <hex_key>] [--ttl <seconds>]

If --key is not provided, reads AES_SECRET_KEY from .env file.

Example:
    python scripts/generate_token.py test_07
    python scripts/generate_token.py test_07 --key abcdef0123456789...
"""
import argparse
import base64
import json
import os
import sys
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from dotenv import load_dotenv


def generate_token(device_name: str, key_hex: str) -> str:
    """Encrypt device_name + timestamp + nonce into a bearer token."""
    key = bytes.fromhex(key_hex)
    payload = json.dumps({
        "device_name": device_name,
        "timestamp": int(time.time()),
        "nonce": os.urandom(4).hex(),
    }).encode("utf-8")

    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(payload, AES.block_size))

    token = base64.urlsafe_b64encode(iv + ciphertext).decode("ascii")
    return token


def main():
    parser = argparse.ArgumentParser(description="Generate AES auth token")
    parser.add_argument("device_name", help="Device name to encrypt")
    parser.add_argument("--key", help="AES key as 64-char hex string (overrides .env)")
    parser.add_argument("--ttl", type=int, default=300, help="Token TTL in seconds (for info only)")
    args = parser.parse_args()

    key_hex = args.key
    if not key_hex:
        load_dotenv()
        key_hex = os.getenv("AES_SECRET_KEY", "")

    if not key_hex or len(key_hex) != 64:
        print("Error: AES_SECRET_KEY must be a 64-char hex string (32 bytes)", file=sys.stderr)
        print("Generate one with: python -c \"import os; print(os.urandom(32).hex())\"", file=sys.stderr)
        sys.exit(1)

    token = generate_token(args.device_name, key_hex)

    print(f"Device:   {args.device_name}")
    print(f"TTL:      {args.ttl}s")
    print(f"Token:    {token}")
    print()
    print("curl example:")
    print(f'  curl -H "Authorization: Bearer {token}" http://localhost:8000/health')


if __name__ == "__main__":
    main()
