# 部署指南 — CS 饰品分析

本文档介绍如何将 **CS 饰品智能分析系统** 部署到服务器或本地长期运行。股票定时分析相关配置（`STOCK_LIST`、交易日历等）见遗留文档 [full-guide.md](full-guide.md)。

## 部署前检查

| 项 | 说明 |
| --- | --- |
| `CSQAQ_API_TOKEN` | 必填；服务器 IP 加入 CSQAQ 白名单 |
| LLM API Key | 必填（若需 AI 报告） |
| 搜索 API Key | 推荐（事件情报） |
| `WEBUI_PORT` | Web 访问端口，默认 `8000` |
| `.env` | **勿提交到 Git**；仅留在服务器本地 |

## 方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
| --- | --- | --- | --- |
| **Docker Compose** | 环境一致、易迁移 | 需安装 Docker | 云服务器长期运行 |
| **直接部署** | 简单 | 需自管 Python/Node | 开发机 / 内网 |
| **仅 API + 本地前端** | 调试方便 | 需两个进程 | 日常开发 |

---

## Docker Compose（推荐）

### 1. 准备

```bash
git clone https://github.com/OMAITL/CS_Analysis.git /opt/cs-analysis
cd /opt/cs-analysis
cp .env.example .env
vim .env   # CSQAQ_API_TOKEN、LLM、搜索 Key、WEBUI_PORT
```

### 2. 启动

```bash
docker-compose -f ./docker/docker-compose.yml up -d
docker-compose -f ./docker/docker-compose.yml logs -f
```

浏览器访问 `http://<服务器IP>:8000`，首页即为饰品 Agent 工作台。

安全组需放行 `WEBUI_PORT`。外网访问细节见 [云端 WebUI 部署](deploy-webui-cloud.md)。

### 3. 更新

```bash
git pull
docker-compose -f ./docker/docker-compose.yml up -d --build
```

---

## 直接部署（API + Web 前端）

### 后端

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

或使用：

```bash
python main.py --serve-only
```

### 前端（生产构建）

```bash
cd apps/dsa-web
npm ci
npm run build
```

将 `dist` 交由 Nginx 托管，并把 `/api` 反向代理到后端。开发模式仍用 `npm run dev`。

---

## Systemd 示例（仅 API）

```ini
[Unit]
Description=CS Analysis API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/cs-analysis
EnvironmentFile=/opt/cs-analysis/.env
ExecStart=/opt/cs-analysis/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 资源与性能建议

| 场景 | 建议 |
| --- | --- |
| 单次 Web 分析 | 1–3 分钟；CPU 中等占用 |
| `refresh_crawl` | 约 30s/饰品；需 Playwright + Chromium |
| 并发 | 默认串行分析为主；过高并发易触发 CSQAQ 限流 |
| 磁盘 | 爬虫 DB、分析 DB 位于 `data/`（已在 `.gitignore`） |

---

## 相关文档

- [CS 使用与配置指南](cs-guide.md)
- [CS 分析技术说明](cs-item-analysis.md)
- [Zeabur 部署](docker/zeabur-deployment.md)
- [桌面端打包](desktop-package.md)
