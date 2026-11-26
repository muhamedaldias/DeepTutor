"""Allow ``python -m deeptutor.mcp_server`` to run the stdio server."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
