"""Giới hạn kích thước thân request ở tầng ASGI (T-04-03) — sao theo
backend/app/core/body_limit.py. Dịch vụ AI chỉ nhận văn bản JSON nên trần là
Settings.MAX_BODY_BYTES (mặc định 8 MiB), quá trần → 413 trước khi Pydantic
hay mô hình chạm vào dữ liệu.

CR-01: `Content-Length` là header do client tự khai — nếu client dùng
`Transfer-Encoding: chunked` (hoặc đơn giản là không gửi header này), giá trị
sẽ là `None` và bản kiểm tra dựa-vào-header-đơn-thuần bị bỏ qua hoàn toàn.
Vì vậy middleware đếm số byte THỰC SỰ đọc được qua `receive()` bất kể header
có mặt hay không — đây mới là tuyến phòng thủ thật sự; kiểm tra header chỉ là
một fast-path để từ chối sớm, không phải tuyến phòng thủ duy nhất.
"""
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_BODY_BYTES = 8 * 1024 * 1024


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
                if int(content_length) > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                pass

        # Fast-path trên không bắt được request chunked / thiếu header. Bọc
        # receive() để đếm byte thật đã đọc — đây là chốt chặn không phụ
        # thuộc Content-Length, đóng lỗ hổng CR-01.
        total = 0
        rejected = False

        async def limited_receive() -> dict:
            nonlocal total, rejected
            if rejected:
                # Đã trả 413; coi như client ngắt kết nối để app dừng đọc
                # tiếp phần thân còn lại thay vì tiếp tục buffer vô hạn.
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    rejected = True
                    await self._reject(scope, receive, send)
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: dict) -> None:
            if rejected:
                # Response 413 đã được gửi trực tiếp qua `send` gốc trong
                # limited_receive; bỏ qua mọi message app cố gửi thêm sau khi
                # nhận http.disconnect để tránh gửi chồng 2 response.
                return
            await send(message)

        await self.app(scope, limited_receive, guarded_send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = PlainTextResponse("Payload Too Large", status_code=413)
        await response(scope, receive, send)
