import os
import sys

from core.config import ConfigError
from core.pipeline import build_pipeline
from ui.dashboard import UiDashboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def bootstrap() -> None:
    config_path = os.path.join(BASE_DIR, "config", "config.json")
    runtime = build_pipeline(BASE_DIR, config_path)
    dashboard = UiDashboard(runtime.ui_queue, runtime.stream_max, runtime.window_size,
                            runtime.chart_defs, runtime.telemetry_flags)
    dashboard.set_shutdown_callback(runtime.stop_components)
    try:
        runtime.start_components()
        dashboard.run()
    finally:
        runtime.stop_components()
        runtime.join_components()


def main() -> None:
    try:
        bootstrap()
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted; shutting down.")
        sys.exit(1)
    except ConfigError as exc:
        print(f"[CONFIG ERROR] {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
