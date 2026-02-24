# SSE Demo (Teaching Version)

This project is a minimal Searchable Symmetric Encryption (SSE) demo:
- Client encrypts documents and builds a keyword->token index.
- Server stores ciphertexts and token->doc_id lists only.
- Client searches by keyword; server returns ciphertexts; client decrypts.

## Security Notes (Teaching Demo)
- Server never sees plaintext or keys.
- Tokens are HMAC(Kt, keyword); server only sees tokens.
- This demo leaks access pattern and result size (standard SSE leakage).

## Structure
- server/: FastAPI server and storage
- client/: client encryption, token generation, upload/search

## Run (Windows)
1) Create venv and install deps
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Start server
```
uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

3) Upload docs
```
python -m client.client upload --file client/demo_docs/doc1.txt
python -m client.client upload --file client/demo_docs/doc2.txt --keywords crypto privacy
```

4) Search
```
python -m client.client search --keyword crypto
python -m client.client search --keyword privacy
```

## Demo Ideas
- Show plaintext files, then upload logs (server sees only tokens).
- Search for keywords like crypto/hello/北京 and show decrypted hits.
- Add your student ID in the final slide/frame.
