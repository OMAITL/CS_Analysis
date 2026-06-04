# 文档中心 — CS 饰品分析

本仓库以 **CS2 饰品投资分析** 为主。README 提供概览与快速开始；详细配置、Web 使用与排障从下文进入。

> 仓库中仍保留部分上游「股票分析」文档（如 `full-guide.md`、`TUSHARE_STOCK_LIST_GUIDE.md`），仅供 `/stocks` 等遗留路由参考，**新用户请优先阅读 CS 专题文档**。

## 按场景选择

| 我想要 | 先看 | 继续看 |
| --- | --- | --- |
| 快速了解能做什么 | [README](../README.md) | [CS 使用与配置指南](cs-guide.md) |
| 第一次跑通 Web 分析 | [CS 使用指南 · 快速开始](cs-guide.md#快速开始) | [CS 分析技术说明](cs-item-analysis.md) |
| 理解数据从哪来 | [CS 分析技术说明](cs-item-analysis.md) | [爬虫说明](../crawlers/README.md)、[CSQAQ 成交量导出](csqaq-volume-crawler.md) |
| 配置大模型 | [LLM 配置指南](LLM_CONFIG_GUIDE.md) | [LLM 服务商配置](llm-providers.md) |
| 配置推送通知 | [通知能力基线](notifications.md) | [部署指南](DEPLOY.md) |
| 部署到服务器 | [部署指南](DEPLOY.md) | [云端 WebUI](deploy-webui-cloud.md) |
| 排查分析问题 | [FAQ](FAQ.md) | [更新日志](CHANGELOG.md) |
| 参与开发 | [贡献指南](CONTRIBUTING.md) | 根目录 [AGENTS.md](../AGENTS.md) |

## CS 专题（推荐）

| 文档 | 内容 |
| --- | --- |
| [CS 使用与配置指南](cs-guide.md) | 环境变量、Web 工作台、CLI、API、排障 |
| [CS 分析技术说明](cs-item-analysis.md) | 数据融合、Skill 介入点、事件情报、API 契约 |
| [HLTV 爬虫](hltv-crawler.md) | 赛事 / 舆论数据源 |
| [CSQAQ 成交量导出](csqaq-volume-crawler.md) | 批量导出成交量 CSV |
| [Web UI 说明](ui-v2-preview.md) | 首页组件结构与路由（工作台已合入 `/`） |

## 通用能力（与饰品共用）

| 文档 | 内容 |
| --- | --- |
| [LLM 配置指南](LLM_CONFIG_GUIDE.md) | 模型渠道与 Web 设置页 |
| [通知能力基线](notifications.md) | 企业微信、飞书、Telegram 等 |
| [Bot 命令与接入](bot-command.md) | IM Bot（若启用） |
| [部署指南](DEPLOY.md) | Docker、云服务器 |
| [桌面端打包](desktop-package.md) | Electron 客户端 |
| [OpenClaw Skill 集成](openclaw-skill-integration.md) | 外部 Skill 集成 |

## 遗留 / 股票相关（可选）

| 文档 | 说明 |
| --- | --- |
| [完整配置与部署指南](full-guide.md) | 上游股票项目长文档 |
| [Tushare 股票列表指南](TUSHARE_STOCK_LIST_GUIDE.md) | 仅 `/stocks` 使用 |
| [图片识别 Prompt](image-extract-prompt.md) | 股票截图导入 |
| [分析上下文包](analysis-context-pack.md) | 股票 AnalysisContextPack |

## 多语言

上游项目提供 [英文索引](INDEX_EN.md)、[英文 README](README_EN.md) 等，内容仍以股票为主；CS 中文文档以本页所列为准。
