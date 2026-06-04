# CS 饰品数据爬虫（与主分析流水线解耦）

本目录存放 **CSQAQ / HLTV / 第三方站点** 的数据抓取脚本，不直接参与股票主流程。

## HLTV 新闻（可选）

| 脚本 / 模块 | 作用 |
| --- | --- |
| `hltv/news_crawler.py` | 低频率读取 HLTV 新闻 sitemap / 列表 |
| `tools/fetch_hltv_news.py` | 命令行测试 |

说明见 [docs/hltv-crawler.md](../docs/hltv-crawler.md)。`.env` 设置 `HLTV_CRAWL_ENABLED=true` 后与 CS 事件情报合并展示。

## CSQAQ 成交量爬虫

对应站点：[CSQAQ 首页](https://csqaq.com/home)

| 脚本 | 作用 |
| --- | --- |
| `csqaq/run_index_volume.py` | 抓取各 **饰品指数** 日 K 成交量 |
| `csqaq/run_item_volume.py` | 抓取 **单品** 日成交量（分页遍历饰品列表） |

### 环境

在项目根目录 `.env` 中配置（与 Phase 1 相同）：

```env
CSQAQ_API_TOKEN=你的Token
CSQAQ_MIN_INTERVAL_SECONDS=1.2
CSQAQ_CRAWL_DB=data/cs_crawl_volume.db
CSQAQ_PRICE_PLATFORM=buff
```

可选 Playwright（用于补抓网页端 chart 响应）：

```bash
pip install -r crawlers/requirements-extra.txt
python -m playwright install chromium
```

### 运行示例

```bash
# 首页全部指数（默认含 id=1 饰品指数）
python crawlers/csqaq/run_index_volume.py

# 指定指数 + 导出 CSV
python crawlers/csqaq/run_index_volume.py --index-id 1 --csv data/cs_index_volume.csv

# 单品：按 good_id 列表
python crawlers/csqaq/run_item_volume.py --good-ids 135,769

# 单品：分页爬取饰品列表（默认最多 3 页，每页 100）
python crawlers/csqaq/run_item_volume.py --max-pages 10 --page-size 100

# 单品：K 线成交量（与网站红框 tooltip 一致，需 Playwright）
python crawlers/csqaq/run_item_volume.py --good-ids 769 --browser-kline --platform yyyp

# 开放 API 回退（挂牌量代理 sell_num，非 K 线成交量）
python crawlers/csqaq/run_item_volume.py --good-ids 769 --platform yyyp
```

### 数据说明（重要）

| 数据 | 来源 | 与网站红框「成交量」关系 |
| --- | --- | --- |
| 指数日成交量 | 开放 API `GET /sub/kline` 字段 `v` | 结构对齐；**免费 Token 下 `v` 可能恒为 0**，需企业接口或网页端另行验证 |
| 单品日 K 成交量 | Playwright 网页 `chartAll` 字段 `v` | 与网站 K 线 tooltip **成交量一致**（需 `--browser-kline`） |
| 单品日 K 成交量 | 企业 API `chartAll` | 同上；直连 Open API 免费 Token 通常 **401** |
| 单品当日成交量快照 | `GET /info/good` → `turnover_number` | 仅 **最新一日快照**，非历史序列 |
| 单品挂牌量代理 | `POST /info/chart` → `num_data` | **不是**成交量，仅作活跃度参考 |

爬虫会在 `volume_source` 字段标注来源，避免与网站 tooltip 混淆。

### 合规

CSQAQ 开放 API 文档声明仅供学习交流；请遵守 [接入指南](https://docs.csqaq.com/doc-4588854.md) 的频率限制（默认 1 次/秒/IP），勿高频轰炸。
