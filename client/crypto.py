from __future__ import annotations
import os
import json
import base64
import hmac
import hashlib
from dataclasses import dataclass
from typing import Iterable, List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def normalize_keyword(w: str) -> str:
    return " ".join(w.strip().lower().split())


def derive_token(key_token: bytes, keyword: str) -> str:
    msg = normalize_keyword(keyword).encode("utf-8")
    tag = hmac.new(key_token, msg, hashlib.sha256).hexdigest()
    return tag


@dataclass
class KeyBundle:
    key_enc: bytes
    key_token: bytes


def load_or_create_keys(path: str) -> KeyBundle:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return KeyBundle(
            key_enc=base64.b64decode(obj["key_enc_b64"]),
            key_token=base64.b64decode(obj["key_token_b64"]),
        )

    key_enc = os.urandom(32)
    key_token = os.urandom(32)
    obj = {
        "key_enc_b64": base64.b64encode(key_enc).decode("utf-8"),
        "key_token_b64": base64.b64encode(key_token).decode("utf-8"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    return KeyBundle(key_enc=key_enc, key_token=key_token)


def encrypt_document(key_enc: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    aesgcm = AESGCM(key_enc)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce + ct


def decrypt_document(key_enc: bytes, blob: bytes, aad: bytes = b"") -> bytes:
    aesgcm = AESGCM(key_enc)
    if len(blob) < 12:
        raise ValueError("ciphertext too short")
    nonce = blob[:12]
    ct = blob[12:]
    return aesgcm.decrypt(nonce, ct, aad)


def make_tokens(key_token: bytes, keywords: Iterable[str]) -> List[str]:
    toks: List[str] = []
    for w in keywords:
        w2 = normalize_keyword(w)
        if not w2:
            continue
        toks.append(derive_token(key_token, w2))
    return sorted(set(toks))
