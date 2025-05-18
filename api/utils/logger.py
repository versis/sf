import datetime
import sys
from typing import Optional

def log(message: str, request_id: Optional[str] = None):
    """Prints a log message with a timestamp and optional request ID."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    prefix = f"[{timestamp}]"
    if request_id:
        prefix += f" [ReqID: {request_id}]"
    print(f"{prefix} {message}")
    sys.stdout.flush() 