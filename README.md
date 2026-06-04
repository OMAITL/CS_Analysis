<div align="center">

# CS 饰品智能分析系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/)

> 基于 AI Agent 的 CS2 饰品投资分析：多平台行情、事件情报、策略 Skill 决策与结构化投资报告

[**功能特性**](#-功能特性) · [**快速开始**](#-快速开始) · [**Web 工作台**](#-web-工作台) · [**文档中心**](docs/INDEX.md)

</div>

## 项目定位

本仓库面向 **CS2 饰品（皮肤）投资分析**，不是股票选股系统。核心能力：

- 按饰品名称 / 皮肤 / `good_id` 发起分析任务
- 融合 CSQAQ 开放 API 与爬虫 K 线，输出技术面信号
- 检索 Major、武器箱、HLTV、贴吧等事件情报
- 注入 13 种交易策略 Skill，生成 JSON 决策仪表盘 + Markdown 报告
- Web **Agent 工作台**：左侧下发任务，右侧展示分层分析报告

股票分析、自选股定时推送、大盘复盘等能力在代码中仍保留于 `/stocks` 等路由，**本仓库文档与默认产品路径以饰品为主**。

## 功能特性

| 能力 | 说明 |
| --- | --- |
| Agent 工作台 | 左栏任务配置（平台、Skill、预设饰品），右栏决策层 / 依据 / 点位 / 价差 / 资讯 / AI 总结 |
| 饰品搜索 | 模糊匹配 CSQAQ `good_id`，多结果时须从下拉选择具体磨损款式 |
| 多平台价格 | 悠悠有品、BUFF、Steam 等，支持价差与套利提示 |
| 事件情报 | 搜索引擎 + 可选官方 RSS / HLTV 爬虫，按相关度分组展示 |
| 策略 Skill | 默认 `bull_trend`，可选缠论、波浪、情绪周期等（见 `strategies/cs/`） |
| CLI / API | `tools/analyze_cs_item.py`、`POST /api/v1/cs/items/analyze` 与 Web 共用后端 |
| 通知与 Bot | 可选企业微信 / 飞书 / Telegram 等（与主项目通知模块相同） |

## 技术栈

| 类型 | 说明 |
| --- | --- |
| 行情与搜索 | [CSQAQ API](https://docs.csqaq.com/)、爬虫 K 线（Playwright）、`ItemOhlcvBuilder` 融合 |
| AI | LiteLLM / Gemini 等（与 `.env` 中 LLM 配置相同） |
| 事件新闻 | Tavily、SerpAPI、Brave 等（与股票新闻检索引擎复用） |
| 前端 | React + Vite（`apps/dsa-web`） |
| 后端 | FastAPI（`server.py`、`api/v1/endpoints/cs.py`） |

## 快速开始

### 1. 环境准备

```bash
git clone https://github.com/OMAITL/CS_Analysis.git
cd CS_Analysis
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中至少配置：

```bash
CSQAQ_API_TOKEN=你的_CSQAQ_Token
# LLM（任选其一，例如）
LITELLM_MODEL=gemini/gemini-2.0-flash
GEMINI_API_KEY=你的_Key
# Web 端口（前后端需一致）
WEBUI_PORT=8000
```

事件情报建议配置至少一个搜索 Key（如 `TAVILY_API_KEYS`）。完整项见 [CS 配置说明](docs/cs-guide.md#环境配置)。

### 2. 启动服务

```bash
# 后端 API
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd apps/dsa-web
npm ci
npm run dev
```

浏览器打开 `http://localhost:5173`（或 `.env` 中 `VITE_DEV_PORT`）。首页 `/` 即为饰品 Agent 工作台。

### 3. 命令行快速分析

```bash
python tools/analyze_cs_item.py --good-id 769 --platform yyyp
python tools/report_cs_item.py --good-id 769 --platform yyyp --print-only
```

首次分析前可选抓取 K 线：

```bash
python crawlers/csqaq/run_item_volume.py --good-ids 769 --browser-kline --platform yyyp
python tools/build_cs_item_ohlcv.py --good-ids 769 --platform yyyp
```

## Web 工作台

| 路径 | 页面 |
| --- | --- |
| `/` | 饰品 Agent 工作台（任务 + 报告分栏） |
| `/chat` | 对话式问股（可挂载 CS 相关 Skill） |
| `/preview/chat` | 问股 UI 预览（可选） |
| `/stocks` | 股票分析（遗留能力，非本仓库主路径） |
| `/settings` | 系统与 LLM 配置 |

使用步骤：

1. 输入饰品名或 `good_id`，从下拉选定具体款式  
2. 选择价格平台与决策 Skill  
3. 点击 **启动 Agent 分析**（通常 1–3 分钟）  
4. 右侧查看评分、建议、点位、平台价差、资讯与完整报告  

界面与模块说明见 [Web 工作台说明](docs/cs-guide.md#web-agent-工作台)。

## API 摘要

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/cs/items/search` | 模糊搜索 `good_id` |
| POST | `/api/v1/cs/items/analyze` | 分析饰品（建议传 `good_id`） |
| GET | `/api/v1/cs/items/skills` | 可用 CS 策略 Skill 列表 |

请求体与响应字段见 `api/v1/schemas/cs.py` 与 [CS 分析技术文档](docs/cs-item-analysis.md)。

## 文档

| 文档 | 内容 |
| --- | --- |
| [文档中心](docs/INDEX.md) | 按场景索引 |
| [CS 使用与配置指南](docs/cs-guide.md) | 环境、Web、CLI、排障 |
| [CS 分析技术说明](docs/cs-item-analysis.md) | 数据流、融合、Skill、API |
| [爬虫说明](crawlers/README.md) | K 线 / 成交量抓取 |
| [LLM 配置](docs/LLM_CONFIG_GUIDE.md) | 大模型渠道 |
| [部署指南](docs/DEPLOY.md) | Docker / 服务器 |
| [FAQ](docs/FAQ.md) | 常见问题 |
| [更新日志](docs/CHANGELOG.md) | 版本变更 |

## 免责声明

本项目仅供学习与研究，**不构成任何投资建议**。饰品市场波动大、流动性差异明显，请自行判断风险。作者不对使用本项目产生的任何损失负责。

## License

[MIT License](LICENSE)
