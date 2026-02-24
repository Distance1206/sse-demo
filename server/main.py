from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import base64

from .storage import load_index, save_index, put_doc, get_doc

app = FastAPI(title="SSE Demo Server", version="0.1")


class UploadRequest(BaseModel):
    doc_id: str = Field(..., description="Document ID chosen by client")
    ciphertext_b64: str = Field(..., description="Encrypted document bytes (base64)")
    tokens: List[str] = Field(..., description="List of search tokens for keywords")


class UploadResponse(BaseModel):
    ok: bool
    stored_doc_id: str
    token_count: int


class SearchResponse(BaseModel):
    token: str
    hits: List[str]


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/upload", response_model=UploadResponse)
def upload(req: UploadRequest):
    try:
        blob = base64.b64decode(req.ciphertext_b64.encode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="ciphertext_b64 is not valid base64")

    put_doc(req.doc_id, blob)

    index = load_index()
    for t in req.tokens:
        index.setdefault(t, [])
        if req.doc_id not in index[t]:
            index[t].append(req.doc_id)
    save_index(index)

    print(f"[server] upload doc_id={req.doc_id}, tokens={len(req.tokens)}")

    return UploadResponse(ok=True, stored_doc_id=req.doc_id, token_count=len(req.tokens))


@app.get("/search", response_model=SearchResponse)
def search(token: str):
    index = load_index()
    doc_ids = index.get(token, [])
    print(f"[server] search token={token[:12]}..., hits={len(doc_ids)}")

    hits: List[str] = []
    for doc_id in doc_ids:
        blob = get_doc(doc_id)
        if blob is None:
            continue
        hits.append(base64.b64encode(blob).decode("utf-8"))
    return SearchResponse(token=token, hits=hits)
