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
- **本地商品库**：首次使用建议执行全量同步（见下文）；同步后搜索优先走本地 SQLite，未命中时再请求 CSQAQ 并写入缓存

### 饰品商品库同步（CSQAQ `get_page_list`）

将 CSQAQ 分页商品目录镜像到主库 `DATABASE_PATH` 的 `cs_item_catalog` 表，减少每次输入时的远程搜索。

**首次全量同步**（需 `CSQAQ_API_TOKEN` 与白名单；全量可能耗时较久，受 1 req/s 限速影响）：

```bash
python scripts/sync_cs_item_catalog.py --mode full
```

**日常增量同步**（刷新首页 + 尾部新页 + 名称变更）：

```bash
python scripts/sync_cs_item_catalog.py --mode incremental
```

中断的全量同步可 `--resume` 续跑。查看状态：

```bash
python scripts/sync_cs_item_catalog.py --status
```

或通过 API：

- `GET /api/v1/cs/items/catalog/status`
- `POST /api/v1/cs/items/catalog/sync?mode=incremental`

相关环境变量（可选）：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `CS_ITEM_CATALOG_LOCAL_SEARCH` | `true` | 本地有数据时优先本地搜索 |
| `CS_ITEM_CATALOG_SYNC_PAGE_SIZE` | `100` | 同步分页大小（最大 500） |
| `CS_ITEM_CATALOG_INCREMENTAL_TAIL_PAGES` | `3` | 增量时刷新末尾页数 |
| `CS_ITEM_CATALOG_UPSERT_ON_REMOTE` | `true` | 远程搜索命中时写入本地缓存 |

### 策略 Skill

- 下拉框选择；空为默认 `bull_trend`  
- 列表来自 `GET /api/v1/cs/items/skills`  
- CS 适配 YAML：`strategies/cs/`；通用技术 skill：`strategies/*.yaml`  

### 饰品持仓

- `/portfolio` — 手动录入或上传库存 App 截图导入；支持 **导入预览**（低置信标红、可改 name/wear/float）、三层饰品匹配、去重提示与确认 commit；页面展示 **持仓风险报告**（集中度、止损接近、价格缺失、平台分布）
- API：
  - `GET /api/v1/cs/holdings/snapshot` — 持仓快照（可选 `page`/`page_size`/`platform` 分页）
  - `GET /api/v1/cs/holdings/risk` — 持仓风险报告（`refresh_prices`、`platform` 可选）
  - `POST /api/v1/cs/holdings/import/preview` — 手动/CSV 条目预览
  - `POST /api/v1/cs/holdings/import/preview/image` — 截图 Vision 预览
  - `POST /api/v1/cs/holdings/import/update` — 更新 draft 并重匹配
  - `POST /api/v1/cs/holdings/import/commit` — 确认入库（`skip_duplicates` 跳过重复）
  - 遗留：`POST /api/v1/cs/holdings/bulk`、`/extract-from-image`
- `/stocks/portfolio` — 遗留股票持仓账本

**智能层：价格告警**

默认 **自动开启**（`CS_HOLDINGS_AUTO_ALERTS_ENABLED=true`），无需手动在 `/alerts` 建规则：

- 导入/新增/修改/删除持仓后，系统自动同步告警规则（`source=cs_auto`）
- 每个有 `good_id` 和购入价的饰品（按 **good_id + 平台** 去重；多次录入合并为 **数量加权平均购入价**），自动生成：
  - **止盈**：市价上破 `均价 × (1 + 止盈%)`（默认 +20%）
  - **止损**：市价下破 `均价 × (1 - 止损%)`（默认 -10%）
- 组合级自动监控：止损接近、集中度、价格缺失

Web 服务（`uvicorn server:app`）启动后会 **后台轮询** 评估告警（默认每 5 分钟，可配 `AGENT_EVENT_MONITOR_INTERVAL_MINUTES`）。触发后写入告警历史，并按通知配置推送。

也可在 `/alerts` 手动追加自定义规则；自动规则可在告警列表中识别（来源 `cs_auto`）。

### 问饰品

- `/chat` — CS 饰品多轮问答（做盘识别、高位出货、平台价差、趋势解读等）；会话 API：`/api/v1/cs/chat/*`
- `/stocks/chat` — 遗留股票问股（需 `AGENT_MODE=true`）

**作答范围（自动识别）**

| 范围 | 典型问法 | 注入数据 |
| --- | --- | --- |
| `market` | 「哪些饰品可能做盘」「最近哪些刀型热度上升」 | 指数/子板块 + **watchlist 抽样扫描**（品类种子饰品技术打分后列出具体名称；非全市场穷尽） |
| `portfolio` | 「我持有的要不要出货」 | `/portfolio` 持仓快照 |
| `single_item` | 从工作台追问某一饰品 | 该饰品融合行情 + 历史分析摘要 |
| `general` | 套利方法论、量价解读等 | 以 Skill 框架为主 |

即使首页/workflow 已关联某一饰品，**全市场类问题**也不会被强制收窄到该单品。

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
