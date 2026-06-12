import React, { useState } from 'react';
import { motion } from 'motion/react';
import { BarChart3, LogOut, Menu } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCsChatStore } from '../../stores/csChatStore';
import { cn } from '../../utils/cn';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { StatusDot } from '../common/StatusDot';
import { ThemeToggle } from '../theme/ThemeToggle';
import { APP_NAV_ITEMS } from './navConfig';

type TopNavProps = {
  onOpenMobileMenu?: () => void;
};

export const TopNav: React.FC<TopNavProps> = ({ onOpenMobileMenu }) => {
  const { authEnabled, logout } = useAuth();
  const completionBadge = useCsChatStore((state) => state.completionBadge);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  return (
    <>
      <header
        className="shell-topnav sticky top-0 z-50 border-b border-border/60 bg-background/90 backdrop-blur-xl"
        data-testid="shell-topnav"
      >
        <div className="shell-topnav-inner mx-auto flex h-14 w-full max-w-[1680px] items-center gap-3 px-3 sm:px-4 lg:px-5">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border/70 bg-card/70 text-secondary-text transition-colors hover:bg-hover hover:text-foreground lg:hidden"
            aria-label="打开导航菜单"
          >
            <Menu className="h-5 w-5" />
          </button>

          <NavLink
            to="/"
            end
            className="flex shrink-0 items-center gap-2 rounded-xl px-1 py-1 transition-colors hover:bg-hover"
            aria-label="饰品投资分析 Agent 首页"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-gradient text-[hsl(var(--primary-foreground))] shadow-[0_8px_20px_var(--nav-brand-shadow)]">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div className="hidden min-w-0 sm:block">
              <p className="truncate text-[0.625rem] font-medium uppercase leading-none tracking-[0.12em] text-secondary-text">
                Multi-Agent Workbench
              </p>
              <p className="truncate text-sm font-semibold leading-tight text-foreground">
                饰品投资分析 Agent
              </p>
            </div>
          </NavLink>

          <nav
            className="shell-topnav-links hidden min-w-0 flex-1 items-center gap-0.5 overflow-x-auto lg:flex"
            aria-label="主导航"
          >
            {APP_NAV_ITEMS.map(({ key, label, to, icon: Icon, exact, badge }) => (
              <NavLink
                key={key}
                to={to}
                end={exact}
                aria-label={label}
                className={({ isActive }) =>
                  cn(
                    'shell-topnav-link group relative flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-[var(--nav-active-bg)] font-medium text-[hsl(var(--primary))]'
                      : 'text-secondary-text hover:bg-[var(--nav-hover-bg)] hover:text-foreground',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive ? (
                      <motion.div
                        layoutId="topNavActiveIndicator"
                        className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-[var(--nav-indicator-bg)]"
                        transition={{ duration: 0.2 }}
                      />
                    ) : null}
                    <Icon className={cn('h-4 w-4 shrink-0', isActive ? 'text-[var(--nav-icon-active)]' : '')} />
                    <span>{label}</span>
                    {badge === 'completion' && completionBadge ? (
                      <StatusDot
                        tone="info"
                        data-testid="chat-completion-badge"
                        className="border-2 border-background"
                        aria-label="问饰品有新消息"
                      />
                    ) : null}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex shrink-0 items-center gap-2">
            <ThemeToggle />
            {authEnabled ? (
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(true)}
                className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-transparent px-2.5 text-sm text-secondary-text transition-colors hover:border-border/70 hover:bg-hover hover:text-foreground"
                aria-label="退出"
              >
                <LogOut className="h-4 w-4 shrink-0" />
                <span className="hidden sm:inline">退出</span>
              </button>
            ) : null}
          </div>
        </div>
      </header>

      <ConfirmDialog
        isOpen={showLogoutConfirm}
        title="退出登录"
        message="确认退出当前登录状态吗？退出后需要重新输入密码。"
        confirmText="确认退出"
        cancelText="取消"
        isDanger
        onConfirm={() => {
          setShowLogoutConfirm(false);
          void logout();
        }}
        onCancel={() => setShowLogoutConfirm(false)}
      />
    </>
  );
};
