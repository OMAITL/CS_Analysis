# CS 单品分析（Phase 2）

Phase 2 在 Phase 1（CSQAQ API + 爬虫）基础上，将 **开放 API 价格序列** 与 **Playwright K 线 OHLCV** 融合为分析级日 K，并接入 `StockTrendAnalyzer`。

## 数据流

```text
开放 API (sell_price) ──┐
                        ├── ItemOhlcvBuilder ── CS_ANALYSIS_DB ── StockTrendAnalyzer
爬虫 chartAll (K线)  ──┘         ▲
                                  │
                         CSQAQ_CRAWL_DB
```

## 环境

`.env` 中除 Phase 1 的 `CSQAQ_*` 外，可选：

```bash
CS_ANALYSIS_DB=data/cs_analysis.db
CSQAQ_CRAWL_DB=data/cs_crawl_volume.db
CSQAQ_PRICE_PLATFORM=yyyp
```

Playwright（仅 `--refresh-crawl` 时需要）：

```bash
pip install -r crawlers/requirements-extra.txt
python -m playwright install chromium
```

## 推荐工作流

### 1. 抓取 K 线（成交量 + 真实 OHLC）

```bash
python crawlers/csqaq/run_item_volume.py --good-ids 769 --browser-kline --platform yyyp
```

### 2. 融合并落库

```bash
python tools/build_cs_item_ohlcv.py --good-ids 769 --platform yyyp
```

或一步刷新爬虫再融合：

```bash
python tools/build_cs_item_ohlcv.py --good-ids 769 --platform yyyp --refresh-crawl
```

### 3. 技术分析

```bash
python tools/analyze_cs_item.py --good-id 769 --platform yyyp
```

或使用名称：

```bash
python tools/analyze_cs_item.py --item "法玛斯 | 机械工业 (崭新出厂)" --platform yyyp
```

导出 JSON 摘要：

```bash
python tools/analyze_cs_item.py --good-id 769 --json data/famas_analysis.json
```

## 融合字段说明

| 字段 | 含义 |
| --- | --- |
| `ohlc_source` | `kline_chart_all` / `sell_price_agg` / `mixed` |
| `volume_source` | `kline_chart_all_v`（网站成交量）/ `sell_num` / `turnover_number` / `none` |
| `data_quality` | `full`（有 K 线成交量）/ `degraded` / `price_only` |

**优先级：** 爬虫 K 线 OHLCV 覆盖同日期 API 数据；API 仅补充更早历史。

## 与 Phase 1 smoke test 的关系

`tools/test_cs_pipeline.py` 已升级为默认读取爬虫 DB 并融合；纯 API 回退：

```bash
python tools/test_cs_pipeline.py --no-crawl
```

## 已知限制

- 指数日 K 成交量（`sub/kline.v`）免费 Token 仍可能为 0，指数分析暂以价格趋势为主。
- `--refresh-crawl` 约 30s/件，批量建议先 crawl 再 build。
- **当天 K 线**：历史日期使用爬虫 DB 缓存；每次分析（API/CLI）默认会轻量重爬最近 1 页（含当天）并 upsert，再与 API 融合。全量历史刷新请用 `--refresh-crawl`。

## Phase 2.3 — LLM Markdown 报告

在 `.env` 中配置 LLM（与股票分析相同，例如 `LITELLM_MODEL` + 对应 API Key）。未配置时自动降级为规则模板报告。

```bash
# 生成报告（默认写入 reports/cs/{good_id}_{name}_{date}.md）
python tools/report_cs_item.py --good-id 769 --platform yyyp

# 分析前刷新 K 线
python tools/report_cs_item.py --item "法玛斯 | 机械工业 (崭新出厂)" --refresh-crawl

# 仅打印到终端
python tools/report_cs_item.py --good-id 769 --print-only
```

报告章节：核心结论 / 技术面解读 / 平台价格与流动性 / **事件与舆论影响** / 风险提示 / 操作建议。

事件情报在每次分析时通过搜索引擎拉取（官方 Blog、Major/贴纸、新箱、HLTV、贴吧、饰品市场），并可选合并 **官方博客 RSS** 与 **HLTV 爬虫**（各维度有条数上限，避免单一来源占满列表）。若 CSQAQ 返回饰品所属武器箱（`container` 字段，如法玛斯「机械工业」→「手套武器箱」），会额外搜索该武器箱相关新闻并标记为「武器箱相关」；搜不到本品或武器箱新闻属正常。需配置 `TAVILY_API_KEYS` 等（与股票新闻相同）。可选：`CS_EVENT_INTEL_ENABLED`、`CS_OFFICIAL_FEED_ENABLED`、`HLTV_CRAWL_ENABLED`、`CS_NEWS_STRATEGY_PROFILE=medium`。

调试相关度（不跑完整分析）：

```bash
venv\Scripts\python.exe tools/probe_cs_event_intel.py --good-id 769
venv\Scripts\python.exe tools/probe_cs_event_intel.py --good-id 769 -v   # 含被过滤条目
```

## Web 前端查看（Phase 2.3+）

1. 启动后端 API：

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

2. 启动前端：

```bash
cd apps/dsa-web
npm ci
npm run dev
```

3. 浏览器打开侧边栏 **「首页」**（`/`），输入饰品名、刀型或皮肤名，**从下拉列表选择具体款式**（含磨损），或输入 `good_id` 后点击 **分析**。原独立页 `/cs` 会重定向到首页；股票分析在 **「股票分析」**（`/stocks`）。

模糊名称（如「蝴蝶刀」「机械工业」）会匹配多个 `good_id`，与 [CSQAQ 获取饰品 ID](https://docs.csqaq.com/api-187131777) 行为一致，必须先选定一条再分析。

页面展示：仪表盘模块（核心洞察、策略点位、运行诊断、资讯等）、技术面摘要；完整 Markdown 报告默认折叠。

API：

- `GET /api/v1/cs/items/search?search=蝴蝶刀&page_size=20` — 模糊搜索 `good_id`（代理 CSQAQ `get_good_id`）
- `POST /api/v1/cs/items/analyze` — 分析（请求体见 `api/v1/schemas/cs.py`）；建议传 `good_id`，仅当名称唯一时再传 `item` 文本

**技能介入点（与股票一致）**：在 `GeminiAnalyzer.analyze()` 生成 JSON 决策仪表盘时，将 CS 白名单 skill 写入 **system prompt**（非仅 Markdown `generate_text`）。LLM 返回 JSON 后由 `src/services/cs_analysis_report.py` 渲染为页面所需的 Markdown 章节。

**CS 可复用技能（13 个）**：7 个纯技术 skill 复用 `strategies/*.yaml`；6 个 CS 适配版在 `strategies/cs/`（事件驱动、热点题材、情绪周期、相对强势、缠论、波浪理论）。默认 `bull_trend`。

**排障：** 若 Web 仅显示 `Internal Server Error`，请先确认后端已启动（端口见根目录 `.env` 的 `WEBUI_PORT`，默认 `uvicorn server:app --port 8000`），前端 `npm run dev` 会从同一 `.env` 读取 `VITE_DEV_PORT`（默认 5173）并代理到 API。
