import argparse
import base64
import os
import re
import requests
from typing import List

from .crypto import (
    load_or_create_keys,
    encrypt_document,
    decrypt_document,
    make_tokens,
    derive_token,
)

DEFAULT_SERVER = "http://127.0.0.1:8000"
KEY_PATH = os.path.join(os.path.dirname(__file__), "client_keys.json")


def simple_extract_keywords(text: str) -> List[str]:
    parts = re.split(r"[^0-9A-Za-z\u4e00-\u9fff]+", text)
    kws: List[str] = []
    for p in parts:
        p = p.strip()
        if len(p) >= 2:
            kws.append(p)
    return kws


def cmd_upload(args):
    keys = load_or_create_keys(KEY_PATH)

    with open(args.file, "rb") as f:
        pt = f.read()

    if args.keywords:
        keywords = args.keywords
    else:
        try:
            text = pt.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
        keywords = simple_extract_keywords(text)

    blob = encrypt_document(keys.key_enc, pt, aad=b"sse-demo-v1")
    tokens = make_tokens(keys.key_token, keywords)

    doc_id = args.doc_id
    if not doc_id:
        base = os.path.basename(args.file)
        doc_id = f"{base}-{len(pt)}"

    payload = {
        "doc_id": doc_id,
        "ciphertext_b64": base64.b64encode(blob).decode("utf-8"),
        "tokens": tokens,
    }
    r = requests.post(f"{args.server}/upload", json=payload, timeout=10)
    r.raise_for_status()
    print("[client] upload ok:", r.json())
    print("[client] keywords(example) =", keywords[:10])
    print("[client] token(example) =", tokens[0][:12] + "..." if tokens else "(none)")


def cmd_search(args):
    keys = load_or_create_keys(KEY_PATH)

    token = derive_token(keys.key_token, args.keyword)
    r = requests.get(f"{args.server}/search", params={"token": token}, timeout=10)
    r.raise_for_status()
    data = r.json()
    hits = data["hits"]
    print(f"[client] search keyword='{args.keyword}', hits={len(hits)}")

    for i, b64 in enumerate(hits, 1):
        blob = base64.b64decode(b64.encode("utf-8"))
        pt = decrypt_document(keys.key_enc, blob, aad=b"sse-demo-v1")
        print(f"\n----- HIT {i} (decrypted) -----")
        try:
            print(pt.decode("utf-8"))
        except Exception:
            print(f"<binary data length={len(pt)}>" )


def main():
    ap = argparse.ArgumentParser(description="SSE Demo Client")
    ap.add_argument("--server", default=DEFAULT_SERVER)

    sub = ap.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upload", help="Encrypt and upload a document with tokens")
    up.add_argument("--file", required=True)
    up.add_argument("--doc-id", default="")
    up.add_argument("--keywords", nargs="*", default=[])
    up.set_defaults(func=cmd_upload)

    se = sub.add_parser("search", help="Search by keyword (client generates token)")
    se.add_argument("--keyword", required=True)
    se.set_defaults(func=cmd_search)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
