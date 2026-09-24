"""Export the FastAPI OpenAPI schema for frontend client generation."""

import argparse
import json
from pathlib import Path

from coupis.api.main import app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(app.openapi(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI schema written to {args.output}")


if __name__ == "__main__":
    main()
