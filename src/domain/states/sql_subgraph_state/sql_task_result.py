from typing_extensions import TypedDict, Any


class SQLTaskResult(TypedDict):
    ok: bool
    rows: list[dict] |  None
    summary: str
    generated_sql: str | None
    error: str | None
    telemetry: dict[str, Any]

