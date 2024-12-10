from typing import Any

try:
    # from truth.truth import AssertThat
    import orjson as json
    from rich.console import Console

    console = Console()
    print = console.print
    JSON_OPTIONS = dict(option=json.OPT_INDENT_2)

except ImportError:
    import json

    JSON_OPTIONS = dict(indent=2)


def as_json(data: dict[str, Any]) -> str:
    return json.dumps(data, **JSON_OPTIONS).decode("utf-8")
