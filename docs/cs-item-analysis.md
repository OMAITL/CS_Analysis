# CS 单品分析 — 技术说明

> 用户向操作说明见 [CS 使用与配置指南](cs-guide.md)；文档索引见 [INDEX.md](INDEX.md)。

在 Phase 1（CSQAQ API + 爬虫）基础上，将 **开放 API 价格序列** 与 **Playwright K 线 OHLCV** 融合为分析级日 K，并接入 `StockTrendAnalyzer`（技术指标与信号逻辑与股票模块复用）。

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

## Web 前端（Agent 工作台）

路由 **`/`** 为饰品分析首页（左任务 / 右报告）。`/cs` 重定向至 `/`；股票分析在 `/stocks`。

### 启动

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
cd apps/dsa-web && npm ci && npm run dev
```

端口以 `.env` 中 `WEBUI_PORT`、`VITE_DEV_PORT` 为准。

### 交互要点

- 搜索：名称 / 皮肤 / `good_id`；多结果须从下拉选定（[CSQAQ get_good_id](https://docs.csqaq.com/api-187131777)）
- 分析：请求体建议带 `good_id`；可选 `platform`、`skills`、`refresh_crawl`
- 报告：`report` 结构化字段 + `report_markdown`；UI 组件见 `apps/dsa-web/src/components/v2/cs/`

### API

| 方法 | 路径 |
| --- | --- |
| GET | `/api/v1/cs/items/search` |
| POST | `/api/v1/cs/items/analyze` |
| GET | `/api/v1/cs/items/skills` |

Schema：`api/v1/schemas/cs.py`。服务实现：`src/services/cs_item_service.py`、`src/services/cs_analysis_report.py`。

### Skill 介入点

在 `GeminiAnalyzer.analyze()` 生成 JSON 决策仪表盘时注入 CS 白名单 skill（**system prompt**），再由 `build_cs_report_payload` / 渲染逻辑输出 Web 与 Markdown。

**13 个 Skill**：7 个通用 `strategies/*.yaml` + 6 个 CS 适配 `strategies/cs/`。默认 `bull_trend`。

### 排障

见 [FAQ.md](FAQ.md) 与 [cs-guide.md](cs-guide.md#排障)。
