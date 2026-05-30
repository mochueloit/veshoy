"""Lanzamiento de Chromium compatible con Docker y servidores Linux."""

import os

from playwright.sync_api import Browser, Playwright


def chromium_launch_args():
    """Flags necesarios dentro de contenedores (sin sandbox, /dev/shm pequeño)."""
    args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--no-first-run",
        "--no-zygote",
    ]
    extra = os.getenv("PLAYWRIGHT_CHROMIUM_ARGS", "")
    if extra.strip():
        args.extend(part.strip() for part in extra.split(",") if part.strip())
    return args


def launch_chromium(playwright: Playwright) -> Browser:
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in {"1", "true", "yes"}
    return playwright.chromium.launch(
        headless=headless,
        args=chromium_launch_args(),
    )
