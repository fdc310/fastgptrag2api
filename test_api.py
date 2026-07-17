"""Quick smoke test for FastGPT RAG API.

Usage:
    python test_api.py <AES_token>
    python test_api.py   # reads token from AES_TOKEN env var
"""
import httpx
import json
import os
import sys

BASE_URL = "http://localhost:8000"
AES_TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.getenv("AES_TOKEN", "")


def _auth():
    return {"Authorization": f"Bearer {AES_TOKEN}"}


def test_health():
    """GET /health"""
    r = httpx.get(f"{BASE_URL}/health", timeout=10)
    print(f"[GET /health] {r.status_code} -> {r.text}")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("  [OK] Health OK\n")


def test_datasets():
    """GET /datasets"""
    r = httpx.get(
        f"{BASE_URL}/datasets",
        headers=_auth(),
        timeout=15,
    )
    print(f"[GET /datasets] {r.status_code}")
    print(f"  {r.text[:300]}")
    if r.status_code == 200:
        print("  [OK] Datasets OK\n")
    else:
        print(f"  [WARN]️  Status {r.status_code}\n")
    return r


def test_collections_list():
    """POST /collections/list"""
    r = httpx.post(
        f"{BASE_URL}/collections/list",
        headers=_auth(),
        json={"offset": 0, "pageSize": 5},
        timeout=15,
    )
    print(f"[POST /collections/list] {r.status_code}")
    print(f"  {r.text[:300]}")
    if r.status_code == 200:
        print("  [OK] Collections list OK\n")
    else:
        print(f"  [WARN]️  Status {r.status_code}\n")
    return r


def test_search():
    """POST /search"""
    r = httpx.post(
        f"{BASE_URL}/search",
        headers=_auth(),
        json={
            "text": "测试搜索",
            "limit": 3,
            "searchMode": "embedding",
        },
        timeout=30,
    )
    print(f"[POST /search] {r.status_code}")
    print(f"  {r.text[:500]}")
    if r.status_code == 200:
        data = r.json().get("data", {})
        count = len(data.get("list", []))
        duration = data.get("duration", "?")
        print(f"  [OK] Search OK | {count} results | {duration}\n")
    else:
        print(f"  [WARN]️  Status {r.status_code}\n")
    return r


def test_search_unauthorized():
    """POST /search without auth -> expect 401"""
    r = httpx.post(
        f"{BASE_URL}/search",
        json={"text": "test"},
        timeout=10,
    )
    print(f"[POST /search no auth] {r.status_code}")
    if r.status_code == 401:
        print("  [OK] Auth guard working (401)\n")
    else:
        print(f"  [WARN]️  Expected 401, got {r.status_code}\n")


def test_search_expired_token():
    """POST /search with expired token -> expect 401"""
    import base64, json, time
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from dotenv import load_dotenv

    load_dotenv()
    key_hex = os.getenv("AES_SECRET_KEY", "")
    key = bytes.fromhex(key_hex)
    payload = json.dumps({"device_name": "test_07", "timestamp": int(time.time()) - 600}).encode()
    iv = os.urandom(16)
    token = base64.urlsafe_b64encode(iv + AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, 16))).decode()

    r = httpx.post(
        f"{BASE_URL}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "test"},
        timeout=10,
    )
    print(f"[POST /search expired token] {r.status_code}")
    if r.status_code == 401:
        print("  [OK] Expired token rejected (401)\n")
    else:
        print(f"  [WARN]️  Expected 401, got {r.status_code}\n")


def test_search_unknown_device():
    """POST /search with unknown device in token -> expect 404"""
    import base64, json, time
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from dotenv import load_dotenv

    load_dotenv()
    key_hex = os.getenv("AES_SECRET_KEY", "")
    key = bytes.fromhex(key_hex)
    payload = json.dumps({"device_name": "nonexistent_device_12345", "timestamp": int(time.time())}).encode()
    iv = os.urandom(16)
    token = base64.urlsafe_b64encode(iv + AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, 16))).decode()

    r = httpx.post(
        f"{BASE_URL}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "test"},
        timeout=10,
    )
    print(f"[POST /search unknown device] {r.status_code}")
    if r.status_code == 404:
        print("  [OK] Device guard working (404)\n")
    else:
        print(f"  [WARN]️  Expected 404, got {r.status_code}\n")


if __name__ == "__main__":
    if not AES_TOKEN:
        print("Usage: python test_api.py <AES_token>")
        print("   or: set AES_TOKEN env var")
        sys.exit(1)

    print("=" * 50)
    print("  FastGPT RAG API Smoke Test")
    print("=" * 50)
    print()

    tests = [
        test_health,
        test_search_unauthorized,
        test_search_expired_token,
        test_search_unknown_device,
        test_datasets,
        test_collections_list,
        test_search,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__} failed: {e}\n")
            failed += 1

    print("=" * 50)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 50)
