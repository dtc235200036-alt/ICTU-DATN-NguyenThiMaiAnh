import threading
import time

from app.core.config import get_settings

ThrottleKey = tuple[str, str]


class LoginThrottle:
    """Đếm số lần đăng nhập sai theo (IP client, mã đăng nhập casefold), trong bộ nhớ.

    An toàn luồng (threading.Lock) — đủ dùng cho một tiến trình uvicorn.
    """

    def __init__(self, max_failures: int, window_minutes: int) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_minutes * 60
        self._lock = threading.Lock()
        self._failures: dict[ThrottleKey, list[float]] = {}

    def _make_key(self, ip: str, dang_nhap: str) -> ThrottleKey:
        return (ip, dang_nhap.casefold())

    def _prune(self, key: ThrottleKey, now: float) -> list[float]:
        cutoff = now - self.window_seconds
        recent = [t for t in self._failures.get(key, []) if t >= cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def is_blocked(self, ip: str, dang_nhap: str) -> bool:
        key = self._make_key(ip, dang_nhap)
        with self._lock:
            recent = self._prune(key, time.time())
            return len(recent) >= self.max_failures

    def record_failure(self, ip: str, dang_nhap: str) -> None:
        key = self._make_key(ip, dang_nhap)
        now = time.time()
        with self._lock:
            recent = self._prune(key, now)
            recent.append(now)
            self._failures[key] = recent

    def reset(self, ip: str, dang_nhap: str) -> None:
        key = self._make_key(ip, dang_nhap)
        with self._lock:
            self._failures.pop(key, None)

    def reset_all(self) -> None:
        with self._lock:
            self._failures.clear()


_settings = get_settings()
login_throttle = LoginThrottle(
    max_failures=_settings.LOGIN_MAX_FAILURES,
    window_minutes=_settings.LOGIN_WINDOW_MINUTES,
)
