import contextvars

trace_id_var = contextvars.ContextVar("X-Trace-ID", default="-")


def set_trace_id(trace_id: str):
    trace_id_var.set(trace_id)


def get_trace_id() -> str:
    print(trace_id_var.get())
    return trace_id_var.get()
