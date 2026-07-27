"""Runtime configuration for StreetNets."""

from __future__ import annotations

import os
from pathlib import Path


def is_hosted() -> bool:
    """Best-effort detection of a hosted deployment (Streamlit Community Cloud).

    Community Cloud containers mount the repo at /mount/src and set
    HOSTNAME=streamlit; either marker means we're not on a user's machine.
    """
    return Path("/mount/src").exists() or os.environ.get("HOSTNAME") == "streamlit"


def deep_analysis_enabled() -> bool:
    """Whether the Deep Analysis page (heavy local computation) is available.

    Deep Analysis can exhaust a shared server's CPU/memory, so it is disabled
    on hosted deployments and enabled everywhere else. The environment
    variable ``STREETNETS_DEEP_ANALYSIS`` overrides the auto-detection in
    both directions ("1"/"true" to force on, "0"/"false" to force off).
    """
    override = os.environ.get("STREETNETS_DEEP_ANALYSIS")
    if override is not None:
        return override.strip().lower() in ("1", "true", "yes", "on")
    return not is_hosted()
