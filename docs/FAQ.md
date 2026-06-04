# CS 饰品分析 — 常见问题

本文档面向 **CS2 饰品分析** 使用场景。股票相关问题见遗留文档 [full-guide.md](full-guide.md)。

---

## 数据与 CSQAQ

### Q1: 提示 CSQAQ Token 无效或 403？

1. 在 [CSQAQ 用户中心](https://csqaq.com) 确认 ApiToken 正确  
2. 将服务器 / 本机公网 IP 加入 **IP 白名单**  
3. 检查 `.env` 中 `CSQAQ_API_TOKEN` 无多余空格或引号  

### Q2: 分析结果没有 K 线成交量？

| `data_quality` | 含义 |
| --- | --- |
| `full` | 爬虫 K 线含成交量 |
| `degraded` / `price_only` |  mainly API 价格序列 |

处理：先跑爬虫再融合：

```bash
python crawlers/csqaq/run_item_volume.py --good-ids <good_id> --browser-kline --platform yyyp
python tools/build_cs_item_ohlcv.py --good-ids <good_id> --platform yyyp
```

### Q3: K 线日期与网站差一天？

项目已按 `Asia/Shanghai` 解析 CSQAQ 日期。若仍异常，检查 `.env` 中 `CSQAQ_MARKET_TIMEZONE`。

### Q4: 价格与悠悠有品 / BUFF 页面不一致？

Web 分析需选择 **价格平台**（`yyyp` / `buff` / `steam`）。不同平台、不同磨损款式价格本身不同；请确认下拉选中的饰品与平台一致。

---

## Web 与分析

### Q5: 输入「蝴蝶刀」后无法分析？

CSQAQ 会返回多个 `good_id`（不同磨损 / 款式）。必须从 **搜索下拉列表** 选定一条后再点「启动 Agent 分析」。仅当名称唯一匹配时才会自动锁定。

### Q6: 分析一直转圈 / 前端超时？

- 完整分析含行情融合、事件情报、LLM，通常 **1–3 分钟**  
- 前端超时已设为约 300 秒；请确认后端未崩溃（看终端日志）  
- 加速：`.env` 设 `CS_EVENT_INTEL_ENABLED=false`，或减小 `CS_EVENT_INTEL_MAX_SEARCHES`  

### Q7: 页面 Internal Server Error？

1. 后端是否启动：`uvicorn server:app --port <WEBUI_PORT>`  
2. 端口是否与 `.env` 的 `WEBUI_PORT`、`VITE` 代理一致  
3. 查看日志中 `active_skills`、CSQAQ、LLM 相关报错  

### Q8: 右侧报告为空？

分析成功前右侧显示占位说明；失败时看顶部黄色 `InlineAlert` 或红色 API 错误条。也可点 **预设任务** 或 **历史分析** 中的记录重试。

### Q9: 历史记录存在哪？

浏览器本地 `localStorage`（`dsa_cs_home_history_v1`），换浏览器或清缓存会丢失。未上传云端。

---

## 事件情报与报告

### Q10: 资讯里很多与本品无关？

系统会按关键词、武器箱、域名过滤；仍可能混入市场要闻。可用 `tools/probe_cs_event_intel.py` 调试。收紧时间窗口：`CS_NEWS_STRATEGY_PROFILE=short`。

### Q11: 没有本品相关新闻是否正常？

正常。冷门饰品可能只有板块 / 武器箱 / 宏观赛事资讯。报告会标注分组（本品相关 / 市场要闻等）。

### Q12: 报告像模板、不够「AI」？

检查 LLM 是否配置成功（`LITELLM_MODEL` + 对应 API Key）。未配置时 `report_source` 可能为 `template` 或 `none`。配置后重试并查看 `report_source` 是否为 LLM 路径。

### Q13: 页面上会看到 `good_id` 吗？

工作台报告 UI 会隐藏 `good_id`、`market_hash_name` 等内部字段；完整 Markdown 折叠区也经前端过滤。API 原始 JSON 仍含这些字段供开发使用。

---

## 配置与部署

### Q14: 必须配置股票用的 `STOCK_LIST` 吗？

**不需要。** 饰品分析只需 `CSQAQ_API_TOKEN` 与 LLM。`STOCK_LIST` 仅股票定时任务使用。

### Q15: Docker 部署后打不开 Web？

1. 映射端口与 `WEBUI_PORT` 一致（默认 8000）  
2. 安全组 / 防火墙放行  
3. 云服务器访问见 [deploy-webui-cloud.md](deploy-webui-cloud.md)  

### Q16: Playwright 在 Windows 上报错？

在虚拟环境中执行 `python -m playwright install chromium`。仅 `--refresh-crawl` / 全量爬虫需要浏览器。

---

## 策略 Skill

### Q17: 有哪些 Skill 可选？

`GET /api/v1/cs/items/skills` 或 Web 下拉列表。默认 `bull_trend`；CS 专用适配见 `strategies/cs/`（事件驱动、情绪周期、缠论等）。

### Q18: Skill 在什么时候生效？

与股票路径一致：在 **`GeminiAnalyzer.analyze()` 生成 JSON 决策仪表盘** 时注入 system prompt，再渲染 Markdown 与 Web `report` 结构。不是仅在最后写报告阶段才注入。

---

## 其他

### Q19: `/stocks` 页面还能用吗？

可以。股票能力为遗留模块，配置与排障见 [full-guide.md](full-guide.md)。本仓库文档默认以 `/` 饰品工作台为主。

### Q20: 如何贡献或反馈问题？

提交 [GitHub Issue](https://github.com/OMAITL/CS_Analysis/issues) 时请说明：`good_id`、平台、是否开启事件情报、后端日志片段（勿贴 Token）。
