<div align="center">

# CS 饰品智能分析系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/)

> 面向 CS2 饰品投资的 AI 分析平台：多平台行情、K 线技术面、事件情报、策略 Skill 与结构化报告，覆盖「单品分析 → 持仓跟踪 → 价格告警 → 每日复盘」

[**功能概览**](#-功能概览) · [**快速开始**](#-快速开始) · [**Web 工作台**](#-web-工作台) · [**项目结构**](#-项目结构) · [**文档中心**](docs/INDEX.md)

</div>

---

## 项目定位

本仓库是 **CS2 饰品（皮肤）投资辅助分析系统**（Daily Stock Analysis / DSA 的 CS 专用分支），**不包含股票选股主流程**。系统围绕 CSQAQ 行情与自研数据融合，帮助用户：

- 对**单个饰品**做技术面 + 事件面 + LLM 综合研判，输出可读的决策报告；
- **管理持仓**、计算盈亏，支持截图批量导入与购入价修正；
- **自动监控**止盈/止损/集中度等规则，并通过邮件、企业微信、Telegram 等渠道推送；
- 通过 **问饰品 Agent** 进行多轮问答（做盘识别、出货建议、市场扫描等）。

> **说明**：早期版本包含 A 股分析能力，当前代码与 Web 路由已 CS 化；访问 `/stocks/*` 等旧路径会自动重定向到 CS 对应页面。

---

## 功能概览

| 模块 | 能力 |
| --- | --- |
| **饰品工作台** | 搜索 `good_id`、选择平台与策略 Skill，一键生成结构化分析报告（评分、建议、点位、价差、资讯） |
| **问饰品** | 多轮对话 Agent，支持全市场扫描、持仓解读、单品追问；SSE 流式回复 |
| **饰品持仓** | 手动录入 / 截图 Vision 导入；内联编辑购入价；刷新 CSQAQ 市价与盈亏 |
| **饰品告警** | 持仓变更后自动同步止盈止损规则；组合级止损接近、集中度、价格过期监控 |
| **每日复盘** | 定时推送 CS 大盘子指数、持仓摘要、涨跌幅榜与 AI 解读（邮件等） |
| **CLI / API** | 与 Web 共用后端，支持脚本化分析与流水线自检 |

---

## 系统架构

```text
┌─────────────────────────────────────────────────────────────────┐
│  Web 前端 (apps/dsa-web)  React + Vite                          │
│  工作台 / 问饰品 / 持仓 / 告警 / 设置                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + SSE
┌────────────────────────────▼────────────────────────────────────┐
│  FastAPI (server.py / api/v1)                                   │
│  cs · alerts · auth · system · usage                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
 market_provider/      src/services/           src/agent/
 csqaq 行情/K线        分析/持仓/告警/报告      CS Agent + Tools
     │                       │                       │
     └───────────┬───────────┴───────────┬───────────┘
                 ▼                       ▼
          SQLite 本地库            LiteLLM / Gemini 等
     (分析 OHLCV / 持仓 / 告警)      事件搜索 + LLM 报告
                 │
                 ▼
          crawlers/csqaq (Playwright K 线 / 榜单)
```

**分析主链路（单品）**

```text
CSQAQ 开放 API (多平台卖价)
        │
        ├── ItemOhlcvBuilder ──► CS_ANALYSIS_DB
        │                              │
爬虫 K 线 (chartAll) ──────────────────┘
                                       ▼
                            StockTrendAnalyzer (MA/RSI/信号)
                                       ▼
              事件情报 (Search + HLTV/官方源) + 策略 Skill (YAML)
                                       ▼
                         LLM 结构化 JSON + Markdown 报告
```

更细的数据契约与字段说明见 [CS 分析技术说明](docs/cs-item-analysis.md)。

---

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 行情 | [CSQAQ Open API](https://docs.csqaq.com/)、Playwright 爬虫 K 线、本地 SQLite 融合库 |
| 技术面 | `StockTrendAnalyzer`（均线、RSI、量能、买卖信号，输入为 CS 融合 OHLCV） |
| AI | LiteLLM 统一接入 Gemini / OpenAI / DeepSeek 等（见 [LLM 配置](docs/LLM_CONFIG_GUIDE.md)） |
| 情报 | Tavily、SerpAPI、Brave 等搜索；可选 HLTV / 官方 RSS |
| 后端 | Python 3.10+、FastAPI、SQLAlchemy |
| 前端 | React 19、Vite、Tailwind、Zustand |
| 通知 | 邮件、企业微信、飞书、Telegram、Pushover、Discord 等（见 [notifications.md](docs/notifications.md)） |
| 部署 | Docker、`main.py --schedule` 定时任务、GitHub Actions（CI） |

---

## 项目结构

```text
.
├── main.py                 # 主入口：Web 服务 / 定时告警与每日报告
├── server.py               # FastAPI 应用导出
├── api/v1/                 # REST API（CS、告警、认证、系统配置）
├── market_provider/csqaq/  # CSQAQ 客户端、K 线适配、报告模板
├── src/
│   ├── services/           # 业务：分析、持仓、告警、每日报告、事件情报
│   ├── agent/              # CS 问饰品 Agent 与 tools
│   ├── stock_analyzer.py   # 技术面引擎（CS/历史命名保留）
│   ├── analyzer.py         # LLM 报告生成
│   └── search_service.py   # 新闻/事件检索
├── strategies/cs/          # 11 个 CS 交易策略 Skill（YAML，含饰品专属类）
├── crawlers/csqaq/         # K 线、成交量、榜单爬虫
├── tools/                  # CLI：分析、报告、流水线自检、CSQAQ 探测
├── apps/dsa-web/           # Web 前端
├── scripts/                # 商品库同步、CI 脚本
├── tests/                  # pytest
└── docs/                   # 专题文档（推荐从 INDEX.md 进入）
```

---

## 快速开始

### 1. 克隆与依赖

```bash
git clone <your-repo-url>
cd daily_stock_analysis-main
pip install -r requirements.txt
cp .env.example .env
```

**可选** — 全量刷新 K 线时需 Playwright：

```bash
pip install -r crawlers/requirements-extra.txt
python -m playwright install chromium
```

### 2. 最小配置（`.env`）

| 变量 | 必填 | 说明 |
| --- | :---: | --- |
| `CSQAQ_API_TOKEN` | ✅ | [CSQAQ](https://csqaq.com) 用户中心 Token，**须绑定服务器公网 IP 白名单** |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` 等 | ✅* | 至少一种 LLM Key |
| `LITELLM_MODEL` | 推荐 | 与 Key 匹配的模型名，如 `gemini/gemini-2.0-flash` |
| `WEBUI_PORT` | 推荐 | 后端端口，默认 `8000` |

\* 未配置 LLM 时，部分路径降级为规则模板报告，质量有限。

**事件情报**（强烈建议至少配置一项搜索 Key）：

```bash
TAVILY_API_KEYS=tvly-xxx
# 或 SERPAPI_API_KEYS、BRAVE_API_KEYS 等
```

完整变量说明见 [CS 使用与配置指南](docs/cs-guide.md#环境配置)。

### 3. 启动 Web

```bash
# 终端 1 — 后端 API
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# 终端 2 — 前端开发服务器
cd apps/dsa-web && npm ci && npm run dev
```

浏览器访问 `http://127.0.0.1:5173`（或 `.env` 中 `VITE_DEV_PORT`）。前端将 `/api` 代理到后端。

**一体化启动**（打包前端静态资源 + API）：

```bash
python main.py --serve-only
```

### 4. 命令行试跑

```bash
# 技术分析摘要
python tools/analyze_cs_item.py --good-id 769 --platform yyyp

# LLM Markdown 报告（需配置 LLM）
python tools/report_cs_item.py --good-id 769 --platform yyyp --print-only

# 流水线自检
python tools/test_cs_pipeline.py
```

首次分析前可选抓取并融合 K 线：

```bash
python crawlers/csqaq/run_item_volume.py --good-ids 769 --browser-kline --platform yyyp
python tools/build_cs_item_ohlcv.py --good-ids 769 --platform yyyp
```

---

## Web 工作台

### 导航与路由

| 路径 | 页面 | 说明 |
| --- | --- | --- |
| `/` | 饰品工作台 | 左侧任务配置，右侧分层分析报告；支持历史记录（localStorage） |
| `/chat` | 问饰品 | 多轮 Agent 对话，流式输出；可关联当前饰品上下文 |
| `/portfolio` | 饰品持仓 | 录入/截图导入、编辑购入价、刷新市价与盈亏 |
| `/alerts` | 饰品告警 | 查看自动/手动规则、触发历史与监控状态 |
| `/settings` | 设置 | LLM、通知、认证等系统配置 |
| `/cs` | 单品页 | 饰品详情与分析入口（部分场景跳转） |
| `/login` | 登录 | 启用 `AUTH_ENABLED` 时出现 |

### 工作台使用步骤

1. 输入饰品名称或 `good_id`，**从下拉选择具体磨损款式**（多匹配时必须确认，避免分析错款）；
2. 选择价格平台（悠悠有品 / BUFF / Steam）与决策 Skill（默认「多头趋势」）；
3. 点击 **启动 Agent 分析**（通常 1–3 分钟，超时约 300 秒）；
4. 右侧查看：**决策层 → 评分依据 → 策略点位 → 平台价差 → 市场资讯 → AI 总结**。

### 问饰品 Agent 范围

| 范围 | 典型问题 | 数据来源 |
| --- | --- | --- |
| 全市场 | 「哪些饰品可能在坐庄」「近期刀型热度」 | 指数/子板块 + watchlist 扫描 |
| 持仓 | 「我持有的要不要出」 | `/portfolio` 持仓快照 |
| 单品 | 从工作台追问某一饰品 | 融合行情 + 分析摘要 |
| 通用 | 套利方法、量价解读 | Skill 框架 + 检索 |

### 持仓与告警（自动化）

- **持仓**：支持手动添加、库存 App **截图识别**导入；购入价可在表格内**铅笔图标** inline 编辑，保存后自动刷新盈亏并同步告警规则。
- **自动告警**（默认开启 `CS_HOLDINGS_AUTO_ALERTS_ENABLED`）：
  - 每个 `good_id + 平台` 按**数量加权平均购入价**生成止盈（默认 +20%）/ 止损（默认 -10%）；
  - 组合级：止损接近、持仓集中度、价格缺失；
  - 后端默认每 **5 分钟**轮询（`AGENT_EVENT_MONITOR_INTERVAL_MINUTES`），触发后邮件等渠道**批量推送**（24h 同规则去重）。

界面细节见 [CS 使用指南 · Web](docs/cs-guide.md#web-agent-工作台)。

---

## 交易策略 Skill

系统在 LLM 报告与 Agent 中注入 **11 个可配置策略 Skill**（`strategies/cs/*.yaml`），通过自然语言描述交易框架，无需写代码：

| 类型 | Skill ID | 说明 |
| --- | --- | --- |
| **饰品专属** | `platform_arbitrage` | 跨平台价差（BUFF / 悠悠 / Steam） |
| **饰品专属** | `major_sticker_cycle` | Major / 贴纸赛事周期 |
| **饰品专属** | `case_supply_chain` | 武器箱供给链与掉率冲击 |
| **饰品专属** | `liquidity_gate` | 流动性门槛（成交笔数 vs 挂牌量） |
| **饰品专属** | `manipulation_radar` | 异常量价 / 做盘嫌疑雷达 |
| 趋势 | `bull_trend` | 默认多头趋势（**默认激活**；含缩量回踩、放量突破分支） |
| 趋势 | `dragon_head` | 相对强势（相对饰品指数） |
| 反转 | `bottom_volume` | 底部放量 |
| 框架 | `box_oscillation` | 箱体震荡 |
| 框架 | `emotion_cycle` | 情绪周期 |
| 框架 | `event_driven` | 事件驱动（Major、新箱、更新、热点题材） |

列表 API：`GET /api/v1/cs/items/skills`。编写自定义策略见 [strategies/README.md](strategies/README.md)。

> CS 与股票的关键差异：无财报/PE/板块涨幅榜；成交量为日成交**笔数**而非挂牌量；驱动因素以赛事、供给、平台价差为主。Skill 注入时会自动忽略股票专用字段语义。

---

## 定时任务与通知

```bash
# 定时：CS 每日复盘邮件 + 后台告警轮询
python main.py --schedule

# 检查通知渠道是否配置正确
python main.py --check-notify
```

| 任务 | 说明 | 相关配置 |
| --- | --- | --- |
| 告警轮询 | `AlertWorker` 评估 CS 规则并推送 | `CS_HOLDINGS_AUTO_ALERTS_ENABLED`、`AGENT_EVENT_MONITOR_*` |
| 每日报告 | 大盘子指数、持仓、涨跌幅榜、AI 总结 | `CS_DAILY_REPORT_ENABLED`、`SCHEDULE_TIME` |

通知渠道在 `.env` 中按项目 [notifications.md](docs/notifications.md) 配置；告警邮件支持 **AI 解读 + 概览表格** 排版。

---

## API 摘要

Base URL：`/api/v1/cs`（完整 Schema 见 `api/v1/schemas/cs.py`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/items/search` | 按名称搜索饰品（优先本地商品库） |
| GET | `/items/catalog/status` | 本地 CSQAQ 商品库同步状态 |
| POST | `/items/catalog/sync` | 全量/增量同步商品库 |
| POST | `/items/analyze` | 单品分析（`good_id`、`platform`、`skills` 等） |
| GET | `/items/skills` | 可用策略 Skill 列表 |
| POST | `/chat/stream` | 问饰品 SSE 流式对话 |
| GET | `/chat/sessions` | 会话列表 |
| GET | `/holdings/snapshot` | 持仓快照与盈亏 |
| GET | `/holdings/risk` | 持仓风险报告 |
| PUT | `/holdings/{id}` | 更新持仓（含购入价） |
| POST | `/holdings/import/preview/image` | 截图导入预览 |
| POST | `/holdings/import/commit` | 确认导入 |

告警相关：`/api/v1/alerts/*`。认证：`/api/v1/auth/*`（可选）。

**分析请求示例**

```http
POST /api/v1/cs/items/analyze
Content-Type: application/json

{
  "good_id": 769,
  "platform": "yyyp",
  "prefer_crawl": true,
  "include_report": true,
  "skills": ["bull_trend", "event_driven"]
}
```

---

## 常用 CLI 工具

| 命令 | 用途 |
| --- | --- |
| `tools/analyze_cs_item.py` | 技术面分析 JSON |
| `tools/report_cs_item.py` | LLM Markdown 报告 |
| `tools/build_cs_item_ohlcv.py` | API + 爬虫 K 线融合落库 |
| `tools/test_cs_pipeline.py` | 端到端流水线自检 |
| `tools/probe_csqaq_api.py` | CSQAQ Token / IP 白名单探测 |
| `tools/probe_cs_event_intel.py` | 事件情报质量调试 |
| `scripts/sync_cs_item_catalog.py` | 同步 CSQAQ 商品目录到本地 |

---

## 开发与验证

```bash
# 后端门禁
./scripts/ci_gate.sh

# 离线单测
python -m pytest -m "not network"

# 前端
cd apps/dsa-web && npm run lint && npm run build
```

协作规范与目录边界见根目录 [AGENTS.md](AGENTS.md)。

---

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [docs/INDEX.md](docs/INDEX.md) | **文档中心**（按场景导航） |
| [docs/cs-guide.md](docs/cs-guide.md) | 环境、Web、CLI、告警、排障 |
| [docs/cs-item-analysis.md](docs/cs-item-analysis.md) | 数据融合、Skill、API 契约 |
| [crawlers/README.md](crawlers/README.md) | K 线 / 成交量爬虫 |
| [docs/LLM_CONFIG_GUIDE.md](docs/LLM_CONFIG_GUIDE.md) | 大模型配置 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Docker / 服务器部署 |
| [docs/notifications.md](docs/notifications.md) | 推送渠道 |
| [docs/FAQ.md](docs/FAQ.md) | 常见问题 |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | 更新日志 |

---

## 免责声明

本项目仅供 **学习与研究**，**不构成任何投资建议**。CS 饰品市场波动大、平台价差与流动性差异显著，历史 K 线与 AI 结论存在延迟与误判可能。请独立判断风险，作者不对使用本项目产生的任何损失负责。

---

## License

[MIT License](LICENSE)
