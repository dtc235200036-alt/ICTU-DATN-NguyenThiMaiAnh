"""CR-01 regression: MaxBodySizeMiddleware phải chặn body vượt ngưỡng ngay cả
khi không có header Content-Length (trường hợp Transfer-Encoding: chunked),
bằng cách đếm byte thực đọc được qua receive() thay vì chỉ tin header."""
import asyncio

from app.core.body_limit import MAX_BODY_BYTES, MaxBodySizeMiddleware


def test_chunked_body_without_content_length_still_gets_413():
    async def downstream_app(scope, receive, send):
        # Giả lập một handler đọc hết thân request, như Starlette/FastAPI làm.
        while True:
            message = await receive()
            if message["type"] == "http.disconnect" or not message.get("more_body", False):
                break

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/topics",
        "headers": [],  # Không có content-length -> mô phỏng chunked transfer.
    }

    chunk = b"a" * 1_048_576  # 1 MiB mỗi lần
    chunks_over_limit = (MAX_BODY_BYTES // len(chunk)) + 2
    state = {"sent": 0}

    async def receive():
        state["sent"] += 1
        if state["sent"] <= chunks_over_limit:
            return {"type": "http.request", "body": chunk, "more_body": True}
        return {"type": "http.request", "body": b"", "more_body": False}

    sent_messages: list[dict] = []

    async def send(message):
        sent_messages.append(message)

    middleware = MaxBodySizeMiddleware(downstream_app)
    asyncio.run(middleware(scope, receive, send))

    starts = [m for m in sent_messages if m["type"] == "http.response.start"]
    assert starts, "middleware phải gửi response khi body vượt MAX_BODY_BYTES"
    assert starts[0]["status"] == 413
