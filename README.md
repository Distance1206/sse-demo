# SSE 演示系统 (Searchable Symmetric Encryption)

本项目实现了一个最小化的 **可搜索对称加密（SSE）系统**。

学号：4125156016
B站演示视频链接：【可搜索加密（SSE）Demo：加密存储 + 关键词查询】 https://www.bilibili.com/video/BV1aff2BvEm8/?share_source=copy_web&vd_source=ee2f9e9f40ed6305806aee3b34b2e750
---

## 1. 背景与动机

当我们将数据存储在不可信服务器（例如云端）时，通常会对文档进行加密以保护隐私。然而，传统加密存在一个问题：

> 一旦数据被加密，就无法在服务器端进行关键词搜索。

**可搜索对称加密（Searchable Symmetric Encryption, SSE）** 解决了这一问题：

- 数据仍然是加密存储
- 服务器无法看到明文内容
- 客户端仍然可以通过关键词进行检索
---

## 2. 密码学设计原理

本系统使用以下标准密码学原语：

### （1）文档加密

- 算法：**AES-GCM（带认证的对称加密算法，AEAD）**
- 作用：
  - 机密性：服务器无法读取文档内容
  - 完整性：若密文被篡改，客户端解密时会检测失败

所有文档均在客户端加密后再上传至服务器。

---

### （2）关键词 Token 生成

对于每个关键词，客户端计算：

token = HMAC(Kt, keyword)


其中：

- HMAC：基于哈希的消息认证码（Hash-based Message Authentication Code）
- `Kt`：仅客户端持有的秘密密钥

token 本质上是关键词的“伪随机标识”。

其性质包括：

- 相同关键词 → 生成相同 token（支持稳定搜索）
- 没有密钥 `Kt`，服务器无法反推出关键词
- token 对服务器而言是随机字符串

---

### （3）加密索引结构

服务器保存：

- 文档密文（ciphertexts）
- 倒排索引结构：

token → [doc_id1, doc_id2, ...]


其中：

- `doc_id` 是文档的唯一标识符
- 服务器通过 token 查找对应文档编号列表

重要说明：

- 服务器看不到明文关键词
- 服务器只看到 token 和文档编号
- 所有解密操作始终在客户端完成
---
### （4）GUI日志说明

GUI 提供日志窗口，用于显示：

- 上传开始与完成信息
- 生成的 token 示例
- 搜索请求信息
- 命中数量
- 错误或异常提示

日志可以用于演示：

- 服务器仅看到 token，而非关键词
- 文档始终以密文形式存储
- 解密操作仅发生在客户端
---

## 3. 搜索流程

当客户端搜索关键词时，流程如下：

1. 客户端计算 `token = HMAC(Kt, keyword)`
2. 客户端将 token 发送给服务器
3. 服务器根据 token 查询索引
4. 返回匹配文档的密文
5. 客户端在本地解密得到明文结果

因此：

- 服务器可以完成“匹配”操作
- 但服务器无法知道具体搜索关键词
- 服务器也无法获取文档明文内容

---

## 4. 安全模型与泄露分析

本项目为教学演示版本 SSE。

安全保证：

- 服务器无法获得文档明文
- 服务器无法直接获得关键词内容
- 加密算法保证数据的机密性与完整性

但系统仍存在典型 SSE 泄露：

- **搜索模式泄露**：相同关键词会生成相同 token
- **访问模式泄露**：服务器知道命中了哪些文档
- **结果大小泄露**：服务器知道每次搜索返回的数量

这些泄露是基础 SSE 设计中的常见权衡。

---

## 5. 项目结构

- `server/`：FastAPI 服务端与存储逻辑
- `client/`：客户端加密、token 生成与上传/搜索逻辑
- `server/data/`：密文文件与索引存储

---

## 6. 运行方式（Windows）

### 1）命令行

python -m venv .venv
..venv\Scripts\activate
pip install -r requirements.txt

启动服务端
uvicorn server.main:app --reload --host 127.0.0.1 --port 8000

上传文档
python -m client.client upload --file client/demo_docs/doc1.txt
python -m client.client upload --file client/demo_docs/doc2.txt --keywords crypto privacy

搜索关键词
python -m client.client search --keyword crypto
python -m client.client search --keyword privacy

### 2）GUI操作

1. 点击“浏览文件”选择明文文档
2. 点击“显示明文”查看原始内容
3. 在关键词输入框中输入关键词（空格分隔）
4. 点击“上传”

系统将：
- 使用 AES-GCM 对文档进行加密
- 对关键词计算 `token = HMAC(Kt, keyword)`
- 上传密文与 token 索引至服务器
- 在日志窗口显示上传成功信息

---

1. 在搜索框输入关键词
2. 点击“搜索”

系统将：
- 在客户端计算对应 token
- 将 token 发送给服务器
- 获取匹配的密文
- 在客户端解密并显示结果

---
