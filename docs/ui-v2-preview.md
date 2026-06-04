# Web 工作台 UI 说明

饰品分析首页已采用 **Agent 工作台** 布局（非预览专用，已合入 `/`）。

## 路由

| 路径 | 页面 |
| --- | --- |
| `/` | 饰品 Agent 工作台（`HomePage` + `IaAgentWorkbench`） |
| `/preview` | 重定向至 `/` |
| `/preview/chat` | 问股 UI 预览 |
| `/chat` | 问股（原版） |
| `/stocks` | 股票分析（遗留） |

## 布局

- **左侧** `IaTaskSidebar`：发起分析任务、预设饰品卡片  
- **右侧** `IaReportPanel` / `IaReportPlaceholder`：报告或空状态  
- **历史** `IaHistoryDrawer`：默认折叠，卡片式本地历史  

## 报告组件（右侧自上而下）

| 组件 | 层级 |
| --- | --- |
| `IaDecisionHero` | 决策：评分、建议、风险、趋势 |
| `IaScoreBreakdown` + `IaSentimentSection` | 依据与情绪 |
| `IaActionZones` | 买入 / 止盈 / 止损 |
| `IaPlatformArbitrage` | 多平台价差 |
| `IaNewsBriefs` | 资讯简讯 |
| `IaAiReport` | AI 总结 + 折叠完整 Markdown |

样式作用域：`.ia-v2-root`（`apps/dsa-web/src/styles/ia-v2.css`）。

## 代码位置

```text
apps/dsa-web/src/
  pages/HomePage.tsx
  components/v2/cs/
  hooks/useCsHomeState.ts
```

业务逻辑与 API 未因 UI 改版而变更；详见 [cs-item-analysis.md](cs-item-analysis.md)。
