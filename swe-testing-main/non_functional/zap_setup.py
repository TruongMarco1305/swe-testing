"""
zap_setup.py — Shared OWASP ZAP availability check for every NFR security test.

Usage in any NFR file
---------------------
    from zap_setup import ensure_zap_ready

    class TestLoginZapScan(unittest.TestCase):
        ZAP_PROXY = "http://127.0.0.1:8080"

        @classmethod
        def setUpClass(cls):
            cls.zap = ensure_zap_ready(cls.ZAP_PROXY)   # raises SkipTest if not ready

What it checks (in order)
-------------------------
1. `pip install python-owasp-zap-v2.4` is installed (the `zapv2` import works).
2. ZAP daemon is reachable at the given proxy address and responds to the API.

If either check fails, a fully-formatted set of install instructions is printed
to stdout and `unittest.SkipTest` is raised so the runner reports a clean SKIP
instead of an ugly traceback.

Platform-aware: shows winget commands on Windows, brew on macOS, apt/snap on
Linux. Also tells the user how to launch the daemon afterwards.
"""

from __future__ import annotations

import os
import platform
import sys
import textwrap
import unittest


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-printed install instructions
# ─────────────────────────────────────────────────────────────────────────────
# Use ASCII-only banner characters so the message renders correctly on every
# Windows console (cp1252) without needing PYTHONIOENCODING tweaks.
_BANNER_TOP = "=" * 72
_BANNER_MID = "-" * 72


def _print_box(title: str, body: str) -> None:
    # Write through sys.stderr.buffer using UTF-8 so the box survives the
    # default cp1252 codepage on Windows consoles. Falls back to print().
    msg = (
        "\n"
        + _BANNER_TOP + "\n"
        + "  " + title + "\n"
        + _BANNER_TOP + "\n"
        + textwrap.dedent(body).rstrip() + "\n"
        + _BANNER_TOP + "\n"
    )
    try:
        sys.stderr.buffer.write(msg.encode("utf-8", errors="replace"))
        sys.stderr.flush()
    except Exception:
        # Last-resort fallback — strip any non-ASCII before printing
        print(msg.encode("ascii", errors="replace").decode("ascii"))


def _install_instructions_python() -> str:
    return """
    The Python client for OWASP ZAP is missing.

    1. Install the client into your current Python environment:

           python -m pip install python-owasp-zap-v2.4

    2. Then re-run the NFR security tests:

           python -m unittest <this_file>.py
    """


def _install_instructions_zap(proxy_url: str) -> str:
    system = platform.system().lower()

    if "windows" in system:
        install_cmds = textwrap.dedent("""
            Option A — winget (recommended on Windows 11):

                winget install --id ZAP.ZAP

            Option B — MSI installer from the official site:

                https://www.zaproxy.org/download/

            ZAP requires Java 17+. If it complains about Java, install it too:

                winget install --id EclipseAdoptium.Temurin.17.JDK
        """).rstrip()

        launch_cmds = textwrap.dedent(f"""
            After installation, start ZAP in headless mode (PowerShell):

                & "C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.bat" `
                    -daemon -port 8080 -config api.disablekey=true

            Verify it is reachable:

                curl http://127.0.0.1:8080/JSON/core/view/version/

            Expected: {{"version":"2.x.x"}}.  Then re-run this test file.
            Daemon must stay open while tests run — leave that PowerShell tab.
        """).rstrip()

    elif "darwin" in system:
        install_cmds = textwrap.dedent("""
            Option A — Homebrew (recommended on macOS):

                brew install --cask zap

            Option B — Download the .dmg from the official site:

                https://www.zaproxy.org/download/

            Java 17+ is also required (Homebrew installs it as a dependency).
        """).rstrip()

        launch_cmds = textwrap.dedent(f"""
            After installation, start ZAP in headless mode:

                /Applications/ZAP.app/Contents/Java/zap.sh \\
                    -daemon -port 8080 -config api.disablekey=true

            Verify it is reachable:

                curl http://127.0.0.1:8080/JSON/core/view/version/

            Then re-run this test file.
        """).rstrip()

    else:  # linux & friends
        install_cmds = textwrap.dedent("""
            Option A — snap (most distros):

                sudo snap install zaproxy --classic

            Option B — apt (Debian/Ubuntu, older versions):

                sudo apt update && sudo apt install zaproxy

            Option C — Download the .tar.gz from the official site:

                https://www.zaproxy.org/download/

            ZAP requires Java 17+ (sudo apt install openjdk-17-jdk).
        """).rstrip()

        launch_cmds = textwrap.dedent(f"""
            After installation, start ZAP in headless mode:

                zap.sh -daemon -port 8080 -config api.disablekey=true

            Verify it is reachable:

                curl http://127.0.0.1:8080/JSON/core/view/version/

            Then re-run this test file.
        """).rstrip()

    return (
        "OWASP ZAP daemon is not reachable at " + proxy_url + ".\n"
        "It must be installed AND running before the security tests can scan.\n\n"
        "INSTALL\n"
        + _BANNER_MID + "\n"
        + install_cmds + "\n\n"
        "RUN AS DAEMON\n"
        + _BANNER_MID + "\n"
        + launch_cmds
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────
def ensure_zap_ready(proxy_url: str = "http://127.0.0.1:8080", timeout: float = 3.0):
    """Return a connected ZAPv2 client, or raise unittest.SkipTest with a
    detailed, platform-aware install guide if anything is missing.

    Steps:
      1. Import the zapv2 Python client.
      2. Construct a client targeting `proxy_url`.
      3. Call zap.core.version — proves the daemon is alive and the API is
         reachable.

    Failures map to SkipTest (not error) so the suite report stays clean."""

    # Step 1 — Python client must be installed
    try:
        from zapv2 import ZAPv2
    except ImportError:
        _print_box("OWASP ZAP — Python client not installed",
                   _install_instructions_python())
        raise unittest.SkipTest(
            "python-owasp-zap-v2.4 is not installed. "
            "See the printed instructions above to install it."
        )

    # Step 2 — Build client
    zap = ZAPv2(proxies={"http": proxy_url, "https": proxy_url})

    # Step 3 — Probe the daemon. Any failure means it's not running / unreachable.
    try:
        # zap.core.version performs an HTTP GET against the API endpoint
        version = zap.core.version
        _ = str(version)         # forces lazy fetch in some zapv2 versions
    except Exception as exc:
        _print_box("OWASP ZAP — daemon not reachable",
                   _install_instructions_zap(proxy_url))
        # Also surface the underlying cause so support can debug if needed
        print(f"  [debug] underlying error: {type(exc).__name__}: {exc}")
        raise unittest.SkipTest(
            f"OWASP ZAP daemon is not reachable at {proxy_url}. "
            "See the printed instructions above to install/start it."
        )

    print(f"  [SEC] ZAP daemon reachable @ {proxy_url} — version {version}")
    return zap
