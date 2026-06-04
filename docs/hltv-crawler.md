# HLTV 新闻爬虫（可选）

HLTV **没有官方开放 API**。本模块仅用于个人研究：低频率读取公开 **新闻 sitemap / 列表页** 的标题与链接，供 CS 饰品「事件与舆论」分析参考。

## 合规与风险（必读）

- 遵守 [HLTV robots.txt](https://www.hltv.org/robots.txt)；勿爬取 `Disallow` 路径（如 `/forums/*`、带复杂查询的 `/stats` 等）。
- 默认 **≥2 秒/请求**（`HLTV_MIN_INTERVAL_SECONDS`），勿并发轰炸。
- 数据仅供个人学习分析，**勿商用、勿二次分发、勿冒充 HLTV**。
- 页面结构变更可能导致解析失败；届时仅回退为空，不影响 CS 技术分析主流程。
- 社区非官方库（如 `hltv-api`）同样存在 ToS/稳定性风险，本仓库采用 **自维护轻量爬虫**，不引入额外 npm 依赖。

## 环境

`.env`：

```bash
# 默认关闭；与 CS 事件情报一起用时打开
HLTV_CRAWL_ENABLED=true
HLTV_CRAWL_MAX_ITEMS=8
HLTV_MIN_INTERVAL_SECONDS=2.0
# HLTV_BASE_URL=https://www.hltv.org
```

需同时开启 CS 事件情报（搜索可选）：

```bash
CS_EVENT_INTEL_ENABLED=true
```

## 数据来源

1. **优先**：`https://www.hltv.org/news-sitemap.xml`（官方新闻 sitemap）
2. **回退**：解析 `https://www.hltv.org/news` 列表中的 `/news/{id}/...` 链接

当前 **不** 抓取比赛细粒度统计、选手 rating、完整正文（降低负载与合规风险）。后续可扩展 Phase 2：赛事列表页。

## 命令行测试

```bash
python tools/fetch_hltv_news.py --max-items 10 -v
```

## 与分析流程的关系

`HLTV_CRAWL_ENABLED=true` 时，每次 CS 饰品分析会在搜索引擎之外 **额外合并** `dimension=hltv_crawl` 条目，并写入报告「事件与舆论影响」章节。
