import json
import os
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DOC_DIR = os.path.join(DATA_DIR, "docs")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")


def _ensure_dirs() -> None:
    os.makedirs(DOC_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def load_index() -> Dict[str, List[str]]:
    _ensure_dirs()
    if not os.path.exists(INDEX_PATH):
        return {}
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index: Dict[str, List[str]]) -> None:
    _ensure_dirs()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def put_doc(doc_id: str, blob: bytes) -> None:
    _ensure_dirs()
    path = os.path.join(DOC_DIR, f"{doc_id}.bin")
    with open(path, "wb") as f:
        f.write(blob)


def get_doc(doc_id: str) -> Optional[bytes]:
    _ensure_dirs()
    path = os.path.join(DOC_DIR, f"{doc_id}.bin")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()
