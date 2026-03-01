# logging_setup.py
import sys
import logging
from datetime import datetime
import platform
import os
import glob
from pathlib import Path

LOG_DIR = "logs"
KEEP_LAST_LOGS = 10

def setup_logging():
    if platform.system() == "Windows":
        base_dir = Path(os.getenv("LOCALAPPDATA"))
    else:
        base_dir = Path.home() / ".local" / "share"
    
    appdata_dir = base_dir / "auto-meeting-subs"

    os.makedirs(appdata_dir/LOG_DIR, exist_ok=True)

    log_file = os.path.join(
        LOG_DIR,
        f"cli_run_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )

    # Auto-delete old logs
    logs = sorted(glob.glob(os.path.join(LOG_DIR, "cli_run_*.log")))
    for old in logs[:-KEEP_LAST_LOGS]:
        try:
            os.remove(old)
        except OSError:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            logging.info("Interrupted by user (Ctrl+C)")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    
    logging.info("==== CLI tool started ====")
    logging.info("Python: %s", platform.python_version())
    logging.info("OS: %s", platform.platform())
    logging.info("CWD: %s", os.getcwd())
