import os
import threading
import time
import base64
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests

from .crypto import (
    load_or_create_keys,
    encrypt_document,
    decrypt_document,
    make_tokens,
    derive_token,
)

DEFAULT_SERVER = "http://127.0.0.1:8000"
KEY_PATH = os.path.join(os.path.dirname(__file__), "client_keys.json")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SSE Demo 图形界面")
        self.geometry("980x680")

        self.keys = load_or_create_keys(KEY_PATH)

        self.server_var = tk.StringVar(value=DEFAULT_SERVER)
        self.file_var = tk.StringVar(value="")
        self.docid_var = tk.StringVar(value="")
        self.keywords_var = tk.StringVar(value="crypto privacy")
        self.search_var = tk.StringVar(value="crypto")

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        # Top: Server settings
        server_frame = ttk.LabelFrame(root, text="服务器", padding=10)
        server_frame.pack(fill=tk.X)

        ttk.Label(server_frame, text="服务器地址：").grid(row=0, column=0, sticky="w")
        ttk.Entry(server_frame, textvariable=self.server_var, width=45).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(server_frame, text="健康检查", command=self.on_health).grid(row=0, column=2, padx=6)

        # Middle: Upload
        upload_frame = ttk.LabelFrame(root, text="上传（加密 + 生成令牌 + 上传）", padding=10)
        upload_frame.pack(fill=tk.X, pady=10)

        ttk.Label(upload_frame, text="文件：").grid(row=0, column=0, sticky="w")
        ttk.Entry(upload_frame, textvariable=self.file_var, width=60).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(upload_frame, text="浏览...", command=self.on_browse).grid(row=0, column=2, padx=6)

        ttk.Label(upload_frame, text="文档 ID（可选）：").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(upload_frame, textvariable=self.docid_var, width=30).grid(row=1, column=1, sticky="w", padx=6, pady=(8, 0))

        ttk.Label(upload_frame, text="关键词（空格分隔）：").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(upload_frame, textvariable=self.keywords_var, width=60).grid(row=2, column=1, sticky="w", padx=6, pady=(8, 0))
        ttk.Button(upload_frame, text="上传", command=self.on_upload).grid(row=2, column=2, padx=6, pady=(8, 0))

        ttk.Button(upload_frame, text="显示明文（预览）", command=self.on_preview).grid(row=1, column=2, padx=6, pady=(8, 0))

        # Middle: Search
        search_frame = ttk.LabelFrame(root, text="搜索（关键词 → 令牌 → 服务端 → 解密）", padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="关键词：").grid(row=0, column=0, sticky="w")
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(search_frame, text="搜索", command=self.on_search).grid(row=0, column=2, padx=6)

        # Bottom: Results + Logs
        bottom = ttk.Frame(root)
        bottom.pack(fill=tk.BOTH, expand=True, pady=10)

        # Results
        res_frame = ttk.LabelFrame(bottom, text="解密结果", padding=10)
        res_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.result_text = tk.Text(res_frame, height=18, wrap="word")
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # Logs
        log_frame = ttk.LabelFrame(bottom, text="日志", padding=10)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.log_text = tk.Text(log_frame, height=18, wrap="word")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        btn_row = ttk.Frame(root)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="清空结果", command=lambda: self.result_text.delete("1.0", tk.END)).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="清空日志", command=lambda: self.log_text.delete("1.0", tk.END)).pack(side=tk.LEFT, padx=8)

    # ---------------- Helpers ----------------
    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)

    def set_results(self, text: str):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)

    def run_bg(self, fn):
        t = threading.Thread(target=fn, daemon=True)
        t.start()

    # ---------------- Actions ----------------
    def on_browse(self):
        path = filedialog.askopenfilename(
            title="选择明文文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.file_var.set(path)
            # default doc id
            base = os.path.basename(path)
            self.docid_var.set(base)

    def on_preview(self):
        path = self.file_var.get().strip()
        if not path:
            messagebox.showwarning("未选择文件", "请先选择文件。")
            return
        if not os.path.exists(path):
            messagebox.showerror("文件不存在", f"文件不存在：\n{path}")
            return
        try:
            with open(path, "rb") as f:
                pt = f.read()
            try:
                text = pt.decode("utf-8")
            except Exception:
                text = f"<二进制数据 长度={len(pt)}>"
            self.set_results(text)
            self.log(f"已预览明文：{path}（{len(pt)} 字节）")
        except Exception as e:
            messagebox.showerror("预览失败", str(e))

    def on_health(self):
        def task():
            url = self.server_var.get().strip().rstrip("/")
            try:
                r = requests.get(f"{url}/health", timeout=5)
                r.raise_for_status()
                self.log(f"健康检查 OK：{r.json()}")
            except Exception as e:
                self.log(f"健康检查失败：{e}")
                messagebox.showerror("健康检查失败", str(e))
        self.run_bg(task)

    def on_upload(self):
        def task():
            url = self.server_var.get().strip().rstrip("/")
            path = self.file_var.get().strip()
            if not path:
                messagebox.showwarning("未选择文件", "请先选择要上传的文件。")
                return
            if not os.path.exists(path):
                messagebox.showerror("文件不存在", f"文件不存在：\n{path}")
                return

            # read plaintext
            with open(path, "rb") as f:
                pt = f.read()

            # keywords
            kw_line = self.keywords_var.get().strip()
            keywords = [k for k in kw_line.split() if k.strip()]
            if not keywords:
                messagebox.showwarning("缺少关键词", "请至少输入 1 个关键词。")
                return

            # doc_id
            doc_id = self.docid_var.get().strip()
            if not doc_id:
                base = os.path.basename(path)
                doc_id = f"{base}-{len(pt)}"

            # crypto
            blob = encrypt_document(self.keys.key_enc, pt, aad=b"sse-demo-v1")
            tokens = make_tokens(self.keys.key_token, keywords)

            payload = {
                "doc_id": doc_id,
                "ciphertext_b64": base64.b64encode(blob).decode("utf-8"),
                "tokens": tokens,
            }

            self.log(f"开始上传：doc_id={doc_id}，文件={os.path.basename(path)}，字节={len(pt)}")
            self.log(f"关键词={keywords}")
            if tokens:
                self.log(f"令牌示例={tokens[0][:12]}...（总数={len(tokens)}）")

            try:
                r = requests.post(f"{url}/upload", json=payload, timeout=10)
                r.raise_for_status()
                self.log(f"上传成功：{r.json()}")
                messagebox.showinfo("上传", "上传成功！")
            except Exception as e:
                self.log(f"上传失败：{e}")
                messagebox.showerror("上传失败", str(e))

        self.run_bg(task)

    def on_search(self):
        def task():
            url = self.server_var.get().strip().rstrip("/")
            kw = self.search_var.get().strip()
            if not kw:
                messagebox.showwarning("缺少关键词", "请输入要搜索的关键词。")
                return

            token = derive_token(self.keys.key_token, kw)
            self.log(f"搜索关键词='{kw}' -> 令牌={token[:12]}...")

            try:
                r = requests.get(f"{url}/search", params={"token": token}, timeout=10)
                r.raise_for_status()
                data = r.json()
                hits = data.get("hits", [])
                self.log(f"搜索返回命中数={len(hits)}")

                if not hits:
                    self.set_results("（无命中）")
                    return

                out_parts = []
                for i, b64 in enumerate(hits, 1):
                    blob = base64.b64decode(b64.encode("utf-8"))
                    try:
                        pt = decrypt_document(self.keys.key_enc, blob, aad=b"sse-demo-v1")
                        try:
                            text = pt.decode("utf-8")
                        except Exception:
                            text = f"<二进制数据 长度={len(pt)}>"
                    except Exception as e:
                        text = f"<解密失败：{e}>"

                    out_parts.append(f"----- 命中 {i} -----\n{text}\n")

                self.set_results("\n".join(out_parts))

            except Exception as e:
                self.log(f"搜索失败：{e}")
                messagebox.showerror("搜索失败", str(e))

        self.run_bg(task)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
