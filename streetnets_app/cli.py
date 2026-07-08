"""Console entry point: `streetnets` launches the Streamlit app."""

import sys
from pathlib import Path


def main() -> None:
    from streamlit.web import cli as stcli

    # Installed package: Home.py is bundled next to this file.
    app = Path(__file__).resolve().parent / "Home.py"
    if not app.exists():
        # Source checkout: Home.py lives at the repo root.
        app = Path(__file__).resolve().parent.parent / "Home.py"
    # Same theme as the repo's .streamlit/config.toml, which installed
    # users don't have. User-provided flags come later, so they win.
    theme = [
        "--theme.base=light",
        "--theme.primaryColor=#2563eb",
        "--theme.backgroundColor=#ffffff",
        "--theme.secondaryBackgroundColor=#f8fafc",
        "--theme.textColor=#1e293b",
    ]
    sys.argv = ["streamlit", "run", str(app), *theme, *sys.argv[1:]]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
