"""Giới hạn kích thước thân request ở tầng ASGI (D-12, NFR-06).

Apache mod_proxy_http không tự thực thi `LimitRequestBody` cho nội dung được
proxy tới backend (giới hạn đã biết của Apache/mod_proxy: giá trị này chỉ áp
dụng cho request được Apache xử lý trực tiếp, ví dụ file tĩnh trong
DocumentRoot — xác minh thực nghiệm khi triển khai kế hoạch này). `ntma.conf`
vẫn khai báo `LimitRequestBody 26214400` (bảo vệ DocumentRoot tĩnh và làm tài
liệu ý định), còn middleware này thực thi lại đúng ngưỡng đó ở tầng ứng dụng
để hành vi quan sát được qua Apache (`deploy/smoke-test.sh`, check h) đúng
như §3.3 mô tả: 21MB đi qua, 30MB nhận 413.
"""
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# Phải khớp giá trị LimitRequestBody trong deploy/apache/ntma.conf.
MAX_BODY_BYTES = 26214400


class MaxBodySizeMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                too_large = int(content_length) > self.max_bytes
            except ValueError:
                too_large = False
            if too_large:
                response = PlainTextResponse("Payload Too Large", status_code=413)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
