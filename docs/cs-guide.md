# CS 饰品分析 — 使用与配置指南

本文档面向 **CS2 饰品投资分析** 用户，涵盖环境配置、Web 工作台、命令行、API 与常见问题。技术实现细节见 [cs-item-analysis.md](cs-item-analysis.md)。

## 快速开始

### 依赖安装

```bash
pip install -r requirements.txt
cp .env.example .env
```

Playwright（仅全量刷新 K 线时需要）：

```bash
pip install -r crawlers/requirements-extra.txt
python -m playwright install chromium
```

### 最小可运行配置

| 变量 | 必填 | 说明 |
| --- | :---: | --- |
| `CSQAQ_API_TOKEN` | ✅ | [CSQAQ](https://csqaq.com) 用户中心 ApiToken，绑定 IP 白名单 |
| `GEMINI_API_KEY` 或 `OPENAI_API_KEY` 等 | ✅* | 至少一种 LLM，用于决策 JSON 与报告 |
| `LITELLM_MODEL` | 推荐 | 与 API Key 对应的模型名 |
| `WEBUI_PORT` | 推荐 | 后端端口，默认 `8000` |

\* 未配置 LLM 时部分路径会降级为规则模板，报告质量有限。

事件情报（推荐至少一项搜索 Key）：

```bash
TAVILY_API_KEYS=tvly-xxx
# 或 SERPAPI_API_KEYS、BRAVE_API_KEYS 等
```

### 启动 Web

```bash
# 终端 1 — API
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# 终端 2 — 前端
cd apps/dsa-web && npm ci && npm run dev
```

访问 `http://127.0.0.1:5173`（以 `VITE_DEV_PORT` 为准）。前端会把 `/api` 代理到 `WEBUI_PORT`。

也可使用：

```bash
python main.py --serve-only
```

## 环境配置

### CSQAQ 与数据库

```bash
CSQAQ_API_TOKEN=
CSQAQ_BASE_URL=https://api.csqaq.com
CSQAQ_PRICE_PLATFORM=yyyp          # 默认价格平台：yyyp / buff / steam
CSQAQ_MARKET_TIMEZONE=Asia/Shanghai
CSQAQ_CACHE_DB=data/cs_csqaq_cache.db
CSQAQ_CRAWL_DB=data/cs_crawl_volume.db
CS_ANALYSIS_DB=data/cs_analysis.db
```

### 事件情报

```bash
CS_EVENT_INTEL_ENABLED=true
CS_EVENT_INTEL_MAX_SEARCHES=8
CS_NEWS_STRATEGY_PROFILE=medium      # 时间窗口档位
CS_OFFICIAL_FEED_ENABLED=true
HLTV_CRAWL_ENABLED=true              # 需爬虫数据，见 hltv-crawler.md
```

调试情报质量（不跑完整分析）：

```bash
python tools/probe_cs_event_intel.py --good-id 769
python tools/probe_cs_event_intel.py --good-id 769 -v
```

### 分析行为

| 场景 | 说明 |
| --- | --- |
| 默认 | 每次分析前轻量刷新「当天」K 线页，再与 API 融合 |
| Web「强制刷新爬虫」 | 对应 API `refresh_crawl=true`，较慢但数据更新 |
| CLI `--refresh-crawl` | 全量重爬后再融合 |

## Web Agent 工作台

路由：`/`（首页）

### 布局

- **左侧**：发起分析任务 — 目标饰品、价格平台、决策 Skill、预设任务卡片  
- **右侧**：分析报告 — 无结果时显示说明与最近历史；分析中显示加载；完成后展示分层报告  

### 报告模块（自上而下）

1. **决策层** — 饰品名、现价、AI 评分、操作建议、风险、趋势  
2. **评分依据** — 利好 / 利空因素、情绪条  
3. **策略点位** — 买入区间、止盈、止损（来自均线等规则字段）  
4. **平台价差** — 多平台价与套利提示  
5. **市场资讯** — 简讯列表，点击展开；利多 / 利空标签  
6. **AI 总结报告** — 结构化摘要 + 可展开完整 Markdown（隐藏 `good_id` 等内部字段）  

### 历史分析

左上角 **历史分析** 按钮展开侧栏；记录保存在浏览器 `localStorage`（键 `dsa_cs_home_history_v1`）。

### 搜索规则

- 支持中文名、英文名、`good_id`  
- 模糊名匹配 **多个** 款式时，必须从下拉选择一条再分析  
- 唯一匹配时会自动锁定 `good_id`  

### 策略 Skill

- 下拉框选择；空为默认 `bull_trend`  
- 列表来自 `GET /api/v1/cs/items/skills`  
- CS 适配 YAML：`strategies/cs/`；通用技术 skill：`strategies/*.yaml`  

### 问股

- `/chat` — 原版多轮对话  
- `/preview/chat` — 简化对话 UI +「高级分析」折叠 Skill  

## 命令行工作流

### 抓取 K 线

```bash
python crawlers/csqaq/run_item_volume.py --good-ids 769 --browser-kline --platform yyyp
```

### 融合 OHLCV

```bash
python tools/build_cs_item_ohlcv.py --good-ids 769 --platform yyyp
python tools/build_cs_item_ohlcv.py --good-ids 769 --refresh-crawl   # 含重爬
```

### 技术分析

```bash
python tools/analyze_cs_item.py --good-id 769 --platform yyyp
python tools/analyze_cs_item.py --item "蝴蝶刀 北方森林" --platform yyyp
```

### LLM 报告

```bash
python tools/report_cs_item.py --good-id 769 --platform yyyp
python tools/report_cs_item.py --good-id 769 --print-only
```

### 流水线自检

```bash
python tools/test_cs_pipeline.py
python tools/test_cs_pipeline.py --no-crawl
```

## API 使用

### 搜索饰品

```http
GET /api/v1/cs/items/search?search=蝴蝶刀&page_size=20
```

### 分析

```http
POST /api/v1/cs/items/analyze
Content-Type: application/json

{
  "good_id": 769,
  "platform": "yyyp",
  "prefer_crawl": true,
  "refresh_crawl": false,
  "include_report": true,
  "skills": ["bull_trend"]
}
```

响应含 `trend`、`snapshot`、`event_intel`、`report`（结构化仪表盘）、`report_markdown` 等。Web 请求超时约 **300 秒**，长分析请耐心等待。

### Skills 列表

```http
GET /api/v1/cs/items/skills
```

## 排障

| 现象 | 处理 |
| --- | --- |
| Web 报 500 / 连不上 API | 确认 `uvicorn` 已启动且端口与 `.env` 的 `WEBUI_PORT` 一致 |
| 前端代理错误 | 确认 `apps/dsa-web` 的 Vite 代理指向正确后端端口 |
| 「未找到饰品」 | 换关键词或从下拉选择；多结果勿直接点分析 |
| 分析超时 | 正常约 1–3 分钟；可关 `CS_EVENT_INTEL` 或减小 `CS_EVENT_INTEL_MAX_SEARCHES` 加速 |
| CSQAQ Token 错误 | 检查白名单 IP 与 Token 是否过期 |
| 报告很「模板化」 | 检查 LLM Key 与 `LITELLM_MODEL`；看日志中 `report_source` |
| 搜不到本品新闻 | 属正常；情报会降级为市场要闻 / 武器箱相关 |

更多问答见 [FAQ.md](FAQ.md)。

## 与股票功能的关系

本仓库代码仍包含股票分析模块（`main.py --stocks`、`/stocks` 页面）。**默认产品与文档以 CS 饰品为准**；股票配置见遗留文档 [full-guide.md](full-guide.md)。
