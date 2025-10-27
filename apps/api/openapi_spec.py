from typing import Any


def generate_openapi_spec(app: Any) -> Any:
    return app.openapi()
