"""Start GuardianEye with settings from config (host 0.0.0.0 by default)."""

from __future__ import annotations

import uvicorn

from config import get_settings


def main() -> None:
    settings = get_settings()
    if settings.is_demo_mode():
        print(
            "\n[GuardianEye] Demo mode — API works without external keys.\n"
            f"  UI + docs: http://127.0.0.1:{settings.port}/  |  http://127.0.0.1:{settings.port}/docs\n"
            "  Live alerts: add ALERTS_API_KEY to backend/.env\n"
            "  Grok AI chat: add GROK_API_KEY to backend/.env\n"
        )
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
