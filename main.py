# -*- coding: utf-8 -*-
"""
===================================
CS 饰品智能分析系统 - 主入口
===================================

职责：
1. 启动 FastAPI 后端与 Web 前端
2. 可选定时运行 CS 告警轮询与每日报告
3. 提供命令行入口

使用方式：
    python main.py              # 启动 Web 服务（若已配置）
    python main.py --serve-only # 仅 Web 服务
    python main.py --schedule   # 定时 CS 告警与每日报告
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from dotenv import dotenv_values
from src.config import setup_env

_INITIAL_PROCESS_ENV = dict(os.environ)
setup_env()

if os.getenv("GITHUB_ACTIONS") != "true" and os.getenv("USE_PROXY", "false").lower() == "true":
    proxy_host = os.getenv("PROXY_HOST", "127.0.0.1")
    proxy_port = os.getenv("PROXY_PORT", "10809")
    proxy_url = f"http://{proxy_host}:{proxy_port}"
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url

from src.webui_frontend import prepare_webui_frontend_assets
from src.config import get_config, Config
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)
_RUNTIME_ENV_FILE_KEYS = set()
_env_bootstrapped = True


def _get_active_env_path() -> Path:
    env_file = os.getenv("ENV_FILE")
    if env_file:
        return Path(env_file)
    return Path(__file__).resolve().parent / ".env"


def _read_active_env_values() -> Optional[Dict[str, str]]:
    env_path = _get_active_env_path()
    if not env_path.exists():
        return {}

    try:
        values = dotenv_values(env_path)
    except Exception as exc:
        logger.warning("读取配置文件 %s 失败，继续沿用当前环境变量: %s", env_path, exc)
        return None

    return {
        str(key): "" if value is None else str(value)
        for key, value in values.items()
        if key is not None
    }


_ACTIVE_ENV_FILE_VALUES = _read_active_env_values() or {}
_RUNTIME_ENV_FILE_KEYS = {
    key for key in _ACTIVE_ENV_FILE_VALUES
    if key not in _INITIAL_PROCESS_ENV
}


def _setup_bootstrap_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)
    if not any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr
        for h in root.handlers
    ):
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        root.addHandler(handler)


def _setup_runtime_logging(log_dir: str, debug: bool = False) -> bool:
    try:
        setup_logging(log_prefix="cs_analysis", debug=debug, log_dir=log_dir)
        return True
    except OSError as exc:
        logger.warning("文件日志初始化失败，已降级为控制台日志输出: %s", exc)
        return False


def _reload_env_file_values_preserving_overrides() -> None:
    global _RUNTIME_ENV_FILE_KEYS

    latest_values = _read_active_env_values()
    if latest_values is None:
        return

    managed_keys = {key for key in latest_values if key not in _INITIAL_PROCESS_ENV}
    for key in _RUNTIME_ENV_FILE_KEYS - managed_keys:
        os.environ.pop(key, None)
    for key in managed_keys:
        os.environ[key] = latest_values[key]
    _RUNTIME_ENV_FILE_KEYS = managed_keys


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CS 饰品智能分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --serve-only    # 仅启动 Web/API 服务
  python main.py --schedule      # 定时 CS 告警轮询
  python main.py --check-notify  # 检查通知配置
        """,
    )
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--check-notify", action="store_true", help="检查通知渠道配置")
    parser.add_argument("--schedule", action="store_true", help="启用定时任务模式")
    parser.add_argument("--no-run-immediately", action="store_true", help="定时任务启动时不立即执行")
    parser.add_argument("--webui", action="store_true", help="启动 Web 管理界面")
    parser.add_argument("--webui-only", action="store_true", help="仅启动 Web 服务")
    parser.add_argument("--serve", action="store_true", help="启动 FastAPI 后端服务")
    parser.add_argument("--serve-only", action="store_true", help="仅启动 FastAPI 后端服务")
    parser.add_argument("--port", type=int, default=8000, help="FastAPI 服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="FastAPI 监听地址")
    return parser.parse_args()


def start_api_server(host: str, port: int, config: Config) -> None:
    import threading
    import uvicorn

    def run_server():
        level_name = (config.log_level or "INFO").lower()
        uvicorn.run("api.app:app", host=host, port=port, log_level=level_name, log_config=None)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("FastAPI 服务已启动: http://%s:%s", host, port)


def _reload_runtime_config() -> Config:
    _reload_env_file_values_preserving_overrides()
    Config.reset_instance()
    return get_config()


def _build_schedule_time_provider(default_schedule_time: str) -> Callable[[], str]:
    from src.core.config_manager import ConfigManager

    system_default = "18:00"
    manager = ConfigManager()

    def _provider() -> str:
        if "SCHEDULE_TIME" in _INITIAL_PROCESS_ENV:
            return os.getenv("SCHEDULE_TIME", default_schedule_time)
        config_map = manager.read_config_map()
        schedule_time = (config_map.get("SCHEDULE_TIME", "") or "").strip()
        return schedule_time or system_default

    return _provider


def main() -> int:
    args = parse_arguments()

    try:
        _setup_bootstrap_logging(debug=args.debug)
    except Exception as exc:
        logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, stream=sys.stderr)
        logger.warning("Bootstrap 日志初始化失败: %s", exc)

    try:
        config = get_config()
    except Exception as exc:
        logger.exception("加载配置失败: %s", exc)
        return 1

    try:
        _setup_runtime_logging(config.log_dir, debug=args.debug)
    except Exception as exc:
        logger.exception("切换到配置日志目录失败: %s", exc)
        return 1

    logger.info("=" * 60)
    logger.info("CS 饰品智能分析系统 启动")
    logger.info("运行时间: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    for warning in config.validate():
        logger.warning(warning)

    if getattr(args, "check_notify", False):
        from src.services.notification_diagnostics import (
            format_notification_diagnostics,
            run_notification_diagnostics,
        )

        result = run_notification_diagnostics(config)
        print(format_notification_diagnostics(result))
        return 0 if result.ok else 1

    if args.webui:
        args.serve = True
    if args.webui_only:
        args.serve_only = True
    if config.webui_enabled and not (args.serve or args.serve_only):
        args.serve = True

    start_serve = (args.serve or args.serve_only) and os.getenv("GITHUB_ACTIONS") != "true"
    if start_serve:
        if args.host == "0.0.0.0" and os.getenv("WEBUI_HOST"):
            args.host = os.getenv("WEBUI_HOST")
        if args.port == 8000 and os.getenv("WEBUI_PORT"):
            args.port = int(os.getenv("WEBUI_PORT"))
        if not prepare_webui_frontend_assets():
            logger.warning("前端静态资源未就绪，继续启动 FastAPI 服务")
        try:
            start_api_server(host=args.host, port=args.port, config=config)
        except Exception as exc:
            logger.error("启动 FastAPI 服务失败: %s", exc)
            return 1

    if args.serve_only and not (args.schedule or config.schedule_enabled):
        logger.info("模式: 仅 Web 服务 (%s:%s)", args.host, args.port)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("用户中断，程序退出")
        return 0

    if args.schedule or config.schedule_enabled:
        logger.info("模式: 定时 CS 告警与每日报告")
        logger.info("每日执行时间: %s", config.schedule_time)
        should_run_immediately = config.schedule_run_immediately and not args.no_run_immediately

        from src.scheduler import run_with_schedule
        from src.services.alert_worker import AlertWorker
        from src.services.cs_daily_report_service import maybe_run_cs_daily_report

        interval_minutes = max(1, getattr(config, "agent_event_monitor_interval_minutes", 5))
        schedule_time_provider = _build_schedule_time_provider(config.schedule_time)

        def scheduled_task():
            runtime_config = _reload_runtime_config()
            if getattr(runtime_config, "cs_daily_report_enabled", False):
                maybe_run_cs_daily_report(config=runtime_config)

        background_tasks = []
        if getattr(config, "agent_event_monitor_enabled", False) or getattr(
            config, "cs_holdings_auto_alerts_enabled", False
        ):
            alert_worker = AlertWorker(config_provider=_reload_runtime_config)

            def event_monitor_task():
                stats = alert_worker.run_once()
                triggered_count = stats.get("triggered", 0)
                if triggered_count:
                    logger.info("[AlertWorker] 本轮触发 %d 条提醒", triggered_count)

            background_tasks.append({
                "task": event_monitor_task,
                "interval_seconds": interval_minutes * 60,
                "run_immediately": True,
                "name": "cs_alert_monitor",
            })

        run_with_schedule(
            task=scheduled_task,
            schedule_time=config.schedule_time,
            run_immediately=should_run_immediately,
            background_tasks=background_tasks,
            schedule_time_provider=schedule_time_provider,
        )
        return 0

    if start_serve:
        logger.info("API 服务运行中 (按 Ctrl+C 退出)...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return 0

    logger.info("未指定运行模式。使用 --serve-only 启动 Web 服务，或 --schedule 启用定时任务。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
