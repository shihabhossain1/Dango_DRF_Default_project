import inspect
import json
from datetime import datetime
from django.utils import timezone


# logging
def log(*args, **kwargs):
    """
    Logs multiple arguments and keyword arguments to a file.
    Pretty-prints JSON strings automatically.
    """
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    formatted_parts = []
    for arg in args:
        # Try to parse JSON strings and pretty print
        if isinstance(arg, str):
            try:
                parsed = json.loads(arg)
                formatted_parts.append(json.dumps(parsed, ensure_ascii=False, indent=2))
                continue
            except Exception:
                pass  # not JSON, keep as string
        # Try to pretty print dict/list/other objects
        try:
            formatted_parts.append(json.dumps(arg, ensure_ascii=False, indent=2, default=str))
        except Exception:
            formatted_parts.append(str(arg))

    if kwargs:
        try:
            formatted_parts.append(json.dumps(kwargs, ensure_ascii=False, indent=2, default=str))
        except Exception:
            formatted_parts.append(str(kwargs))

    message = " ".join(formatted_parts)

    with open('inspector.log', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {filename}:{lineno}\n{message}\n\n")