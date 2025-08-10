import uuid
import contextvars

# Context variable to store correlation id per logical request/update
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default=None)


def new_correlation_id() -> str:
    cid = uuid.uuid4().hex[:12]
    correlation_id_var.set(cid)
    return cid


def get_correlation_id() -> str:
    cid = correlation_id_var.get()
    if not cid:
        cid = new_correlation_id()
    return cid 