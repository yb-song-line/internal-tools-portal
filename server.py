from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
CONFIG_PATH = ROOT / "config" / "tools.json"
SESSION_COOKIE = "tools_portal_session"
LOGIN_WINDOW_SECONDS = 10 * 60
MAX_LOGIN_FAILURES = 6
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._@-]{1,80}$")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    portal = config.get("portal")
    tools = config.get("tools")
    if not isinstance(portal, dict) or not isinstance(tools, list):
        raise RuntimeError("tools.json must contain portal and tools")
    seen_ids: set[str] = set()
    for tool in tools:
        tool_id = tool.get("id", "")
        if not ID_PATTERN.fullmatch(tool_id) or tool_id in seen_ids:
            raise RuntimeError(f"Invalid or duplicate tool id: {tool_id!r}")
        seen_ids.add(tool_id)
        for field in ("name", "description", "category", "url"):
            if not isinstance(tool.get(field), str) or not tool[field].strip():
                raise RuntimeError(f"Tool {tool_id!r} is missing {field}")
        parsed = urlparse(tool["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(f"Tool {tool_id!r} has an invalid URL")
    config["tools"] = sorted(
        (tool for tool in tools if tool.get("enabled", True)),
        key=lambda item: (int(item.get("order", 9999)), item["name"]),
    )
    return config


CONFIG = load_config()
PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "team").strip()
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
DEV_BYPASS = os.environ.get("PORTAL_DEV_BYPASS") == "1"
SESSION_TTL_SECONDS = int(float(os.environ.get("SESSION_TTL_HOURS", "12")) * 3600)

if not USERNAME_PATTERN.fullmatch(PORTAL_USERNAME):
    raise RuntimeError("PORTAL_USERNAME contains unsupported characters")
if not DEV_BYPASS and (len(PORTAL_PASSWORD) < 10 or len(SESSION_SECRET) < 32):
    raise RuntimeError(
        "Set PORTAL_PASSWORD (10+ chars) and SESSION_SECRET (32+ chars). "
        "Use PORTAL_DEV_BYPASS=1 only for local development."
    )
if DEV_BYPASS and not SESSION_SECRET:
    SESSION_SECRET = secrets.token_urlsafe(32)

FAILED_LOGINS: dict[str, deque[float]] = defaultdict(deque)


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_session(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(12),
    }
    encoded = b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = b64url_encode(
        hmac.new(SESSION_SECRET.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{encoded}.{signature}"


def validate_session(token: str) -> bool:
    try:
        encoded, signature = token.split(".", 1)
        expected = b64url_encode(
            hmac.new(SESSION_SECRET.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return False
        payload = json.loads(b64url_decode(encoded))
        return payload.get("sub") == PORTAL_USERNAME and int(payload.get("exp", 0)) > time.time()
    except (ValueError, TypeError, json.JSONDecodeError):
        return False


def prune_failures(client_ip: str) -> deque[float]:
    failures = FAILED_LOGINS[client_ip]
    threshold = time.time() - LOGIN_WINDOW_SECONDS
    while failures and failures[0] < threshold:
        failures.popleft()
    return failures


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "InternalToolsPortal/1.0"

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"{self.address_string()} - {format_string % args}", flush=True)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'",
        )
        super().end_headers()

    @property
    def path_only(self) -> str:
        return urlparse(self.path).path

    @property
    def client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
        return forwarded or self.client_address[0]

    def is_authenticated(self) -> bool:
        if DEV_BYPASS and self.client_ip in {"127.0.0.1", "::1"}:
            return True
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get(SESSION_COOKIE)
        return bool(morsel and validate_session(morsel.value))

    def send_bytes(
        self,
        body: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
        cache_control: str = "no-store",
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_bytes(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def redirect(self, location: str, status: HTTPStatus = HTTPStatus.SEE_OTHER) -> None:
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def serve_static(self, relative_path: str, cache: bool = True) -> None:
        target = (STATIC_DIR / relative_path).resolve()
        if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "image/svg+xml"}:
            content_type += "; charset=utf-8"
        self.send_bytes(
            target.read_bytes(),
            content_type,
            cache_control="public, max-age=3600" if cache else "no-store",
        )

    def require_authentication(self) -> bool:
        if self.is_authenticated():
            return True
        if self.path_only.startswith("/api/"):
            self.send_json({"error": "authentication_required"}, HTTPStatus.UNAUTHORIZED)
        else:
            self.redirect("/login")
        return False

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        path = self.path_only
        if path == "/healthz":
            self.send_json({"status": "ok", "tools": len(CONFIG["tools"])})
            return
        if path in {"/static/styles.css", "/static/login.js", "/favicon.svg", "/favicon.ico"}:
            relative_path = (
                "favicon.svg"
                if path in {"/favicon.svg", "/favicon.ico"}
                else path.removeprefix("/static/")
            )
            self.serve_static(relative_path)
            return
        if path == "/login":
            if self.is_authenticated():
                self.redirect("/")
            else:
                self.serve_static("login.html", cache=False)
            return
        if not self.require_authentication():
            return
        if path == "/":
            self.serve_static("index.html", cache=False)
        elif path == "/api/tools":
            self.send_json(CONFIG)
        elif path.startswith("/static/"):
            self.serve_static(path.removeprefix("/static/"))
        elif path == "/favicon.svg":
            self.serve_static("favicon.svg")
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = self.path_only
        if path == "/login":
            self.handle_login()
        elif path == "/logout":
            cookie = f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"
            if self.headers.get("X-Forwarded-Proto", "").lower() == "https":
                cookie += "; Secure"
            self.redirect("/login", extra_headers={"Set-Cookie": cookie})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def redirect(
        self,
        location: str,
        status: HTTPStatus = HTTPStatus.SEE_OTHER,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()

    def handle_login(self) -> None:
        failures = prune_failures(self.client_ip)
        if len(failures) >= MAX_LOGIN_FAILURES:
            self.send_json(
                {"error": "too_many_attempts", "message": "잠시 후 다시 시도해 주세요."},
                HTTPStatus.TOO_MANY_REQUESTS,
            )
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length <= 0 or content_length > 4096:
            self.send_json({"error": "invalid_request"}, HTTPStatus.BAD_REQUEST)
            return
        values = parse_qs(self.rfile.read(content_length).decode("utf-8", "replace"))
        username = values.get("username", [""])[0]
        password = values.get("password", [""])[0]
        valid = hmac.compare_digest(username, PORTAL_USERNAME) and hmac.compare_digest(
            password, PORTAL_PASSWORD
        )
        if not valid:
            failures.append(time.time())
            self.redirect("/login?error=1")
            return
        FAILED_LOGINS.pop(self.client_ip, None)
        token = create_session(username)
        cookie = (
            f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; "
            f"Max-Age={SESSION_TTL_SECONDS}"
        )
        if self.headers.get("X-Forwarded-Proto", "").lower() == "https":
            cookie += "; Secure"
        self.redirect("/", extra_headers={"Set-Cookie": cookie})


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8787"))
    server = ThreadingHTTPServer((host, port), PortalHandler)
    print(f"Internal tools portal listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
