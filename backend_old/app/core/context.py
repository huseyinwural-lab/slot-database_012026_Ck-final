from contextvars import ContextVar
from typing import Optional, Dict

_log_context: ContextVar[Dict[str, str]] = ContextVar("log_context", default={})

def get_log_context() -> Dict[str, str]:
    return _log_context.get()

def set_log_context(**kwargs):
    ctx = _log_context.get().copy()
    ctx.update(kwargs)
    _log_context.set(ctx)

def clear_log_context():
    _log_context.set({})
