import type React from 'react';
import { BarChart3, Bell, BriefcaseBusiness, Home, MessageSquareQuote, Settings2, TrendingUp } from 'lucide-react';

export type AppNavItem = {
  key: string;
  label: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
  badge?: 'completion';
};

export const APP_NAV_ITEMS: AppNavItem[] = [
  { key: 'home', label: '首页', to: '/', icon: Home, exact: true },
  { key: 'stocks', label: '股票分析', to: '/stocks', icon: TrendingUp },
  { key: 'chat', label: '问饰品', to: '/chat', icon: MessageSquareQuote, badge: 'completion' },
  { key: 'portfolio', label: '持仓', to: '/portfolio', icon: BriefcaseBusiness },
  { key: 'backtest', label: '回测', to: '/backtest', icon: BarChart3 },
  { key: 'alerts', label: '告警', to: '/alerts', icon: Bell },
  { key: 'settings', label: '设置', to: '/settings', icon: Settings2 },
];
