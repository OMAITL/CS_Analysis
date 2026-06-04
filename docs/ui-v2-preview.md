# 饰品投资助手 UI（v2）

CS 首页 `/` 已采用 Agent 工作台布局（左任务 / 右报告）。组件位于 `apps/dsa-web/src/components/v2/cs/`。

## 访问入口

| 路径 | 页面 | 说明 |
| --- | --- | --- |
| `/` | `HomePage` | 饰品 Agent 工作台（正式首页） |
| `/preview` | — | 重定向至 `/` |
| `/preview/chat` | `ChatPageV2` | 问股 UI 预览（ChatGPT 风格） |

本地开发示例（端口以 `.env` 中 `VITE_DEV_PORT` 为准）：

```text
http://localhost:5176/
http://localhost:5176/preview/chat
```

## 目录结构

```text
apps/dsa-web/src/
  pages/v2/
    HomePageV2.tsx      # 预览首页编排
    ChatPageV2.tsx      # 预览问股
  components/v2/cs/     # 饰品分析 UI 组件
    IaLandingHero.tsx
    IaHistoryDrawer.tsx
    IaReportView.tsx    # 结果页组合（决策→原因→操作→资讯→报告）
    ...
  styles/ia-v2.css      # 预览专用样式（.ia-v2-root 作用域）
```

## 设计对照

| 需求 | 预览实现 |
| --- | --- |
| 左右分栏工作台 | 左 `IaTaskSidebar`（任务下发）· 右 `IaReportPanel` / 空状态占位 |
| 历史栏默认折叠 | `IaHistoryDrawer`，`historyOpen` 初始 `false` |
| 历史卡片化 | 评分 / 建议 / 日期 + 悬停删除 |
| 结果分层 | `IaDecisionHero` → `IaScoreBreakdown` / `IaSentimentSection` → `IaActionZones` → `IaPlatformArbitrage` → `IaNewsBriefs` → `IaAiReport` |
| 情绪条 | `IaSentimentBar` |
| 平台价差 | `IaPlatformArbitrage` |
| 资讯简讯 | `IaNewsBriefs` |
| 报告去内部字段 | `IaAiReport` + `stripInternalReportFields` |
| 问股简化 | `ChatPageV2` 居中输入 + 推荐问题 + `details` 高级策略 |

## 状态与逻辑复用

- 分析流程：`useCsHomeState`（与正式 `HomePage` 相同 hook、同一 `localStorage` 历史键）
- 问股流：`useAgentChatStore.startStream`（与正式 `ChatPage` 相同会话存储）
- 搜索联想：`CsItemSearchInput` + `csApi.searchItems`

## 合入状态

- 首页 `/` 已使用 v2 工作台（`pages/HomePage.tsx` → `IaAgentWorkbench`）。
- 问股 `/chat` 仍为原版；`/preview/chat` 为问股 v2 预览。

回滚首页：恢复 `pages/HomePage.tsx` 旧实现并改回 `App.tsx` 路由即可。
