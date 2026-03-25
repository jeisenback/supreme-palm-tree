"""Secrets helper: optional dotenv loading and typed access.

Usage:
    from agents.secrets import get_env, load_dotenv
    load_dotenv()  # optional (loads .env if present)
    key = get_env("ANTHROPIC_API_KEY", required=False)
"""
from __future__ import annotations

import os
from typing import Optional


def load_dotenv(path: Optional[str] = None) -> None:
    """Load a .env file into the environment if python-dotenv is available.

    This is optional: the function silently returns if `dotenv` is not installed.
    """
    try:
        from dotenv import load_dotenv as _load
    except Exception:
        return
    _load(path or ".env")


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    val = os.environ.get(key, default)
    if required and not val:
        raise EnvironmentError(f"Required env var '{key}' not set")
    return val


def required_keys_present(keys: list[str]) -> bool:
    missing = [k for k in keys if not os.environ.get(k)]
    return len(missing) == 0
