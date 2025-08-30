from datetime import datetime, timezone
from typing import Any, Dict

def make_log_entry(actor: str, action: str, details: Any) -> Dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "details": details
    }
