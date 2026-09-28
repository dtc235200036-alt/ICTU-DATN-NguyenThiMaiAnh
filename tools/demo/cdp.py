"""Trình điều khiển Chrome headless tối giản qua Chrome DevTools Protocol (CDP).

Chỉ dùng thư viện chuẩn + gói `websockets` có sẵn trên máy (không cài thêm
Playwright/Puppeteer). Dùng cho tools/demo/chay-kich-ban.py (plan 05-05, D-04):

    async with TrinhDuyet(base_url) as td:
        await td.dang_nhap("bomon", mat_khau)
        await td.mo("/tong-quan")
        await td.cho_chu("Tổng quan")
        await td.chup("anh.png")

Bảo mật (T-05-17/T-05-18): cổng debug chỉ bind 127.0.0.1 và là cổng tạm
(`--remote-debugging-port=0`), profile tạm bị xóa và Chrome bị kill trong
`finally`; mật khẩu chỉ đi vào thân một `fetch` trong trang, access token không
bao giờ rời trang — module này không in/ghi mật khẩu hay token.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import websockets

RONG = 1440
CAO = 900


class LoiTrinhDuyet(RuntimeError):
    """Lỗi điều khiển trình duyệt (hết giờ chờ, không thấy phần tử...)."""


# JS dùng chung: tìm phần tử theo chữ hiển thị hoặc CSS selector, ưu tiên lớp
# phủ đang mở (modal/drawer/dropdown) trên cùng.
_JS_TIM = r"""
(() => {
  const hienThi = (el) => {
    if (!el || !el.isConnected) return false;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
  };
  const chuan = (t) => (t || '').replace(/\s+/g, ' ').trim();
  const LOP_PHU = '.ant-modal-wrap, .ant-drawer-content-wrapper, .ant-dropdown, .ant-select-dropdown, .ant-popover, .ant-popconfirm';
  window.__ntmaTim = (muc, phamVi, hang) => {
    let goc = document;
    if (hang) {
      const hs = [...document.querySelectorAll('tr, .ant-list-item, .ant-card, .ant-collapse-item')]
        .filter((h) => hienThi(h) && chuan(h.innerText).includes(hang));
      if (!hs.length) return null;
      goc = hs[0];
    }
    if (phamVi) {
      const ds = [...goc.querySelectorAll(phamVi)].filter(hienThi);
      if (!ds.length) return null;
      goc = ds[ds.length - 1];
    }
    // CSS selector trước
    if (/^[#.\[]|^(input|textarea|button|a|div|span|label|li|tr|td)\b/.test(muc)) {
      try {
        const els = [...goc.querySelectorAll(muc)].filter(hienThi);
        if (els.length) return els[0];
      } catch (e) { /* không phải selector hợp lệ -> tìm theo chữ */ }
    }
    const CHON = 'button, a, [role=button], [role=menuitem], [role=tab], [role=option], [role=switch], [role=checkbox], .ant-menu-item, .ant-tabs-tab, .ant-select-item-option, .ant-dropdown-menu-item, .ant-radio-button-wrapper, .ant-checkbox-wrapper, .ant-collapse-header, .ant-badge, .ant-tag, label, th, td, span, div';
    const tatCa = [...goc.querySelectorAll(CHON)].filter(hienThi);
    const muc2 = chuan(muc);
    let khop = tatCa.filter((el) => chuan(el.innerText) === muc2 || el.getAttribute('aria-label') === muc2 || el.getAttribute('title') === muc2);
    if (!khop.length) khop = tatCa.filter((el) => chuan(el.innerText).includes(muc2) && chuan(el.innerText).length <= muc2.length + 40);
    if (!khop.length) return null;
    // Bỏ phần tử cha nếu một phần tử con cũng khớp (lấy phần tử sâu nhất).
    khop = khop.filter((el) => !khop.some((k) => k !== el && el.contains(k)));
    // Ưu tiên phần tử bấm được gần nhất.
    const bamDuoc = (el) => el.closest('button, a, [role=button], [role=menuitem], [role=tab], [role=option], .ant-menu-item, .ant-tabs-tab, .ant-select-item-option, .ant-dropdown-menu-item, .ant-radio-button-wrapper, .ant-checkbox-wrapper, .ant-collapse-header') || el;
    const trongLopPhu = khop.filter((el) => el.closest(LOP_PHU));
    const ds = trongLopPhu.length ? trongLopPhu : khop;
    return bamDuoc(ds[ds.length && trongLopPhu.length ? ds.length - 1 : 0]);
  };
  window.__ntmaO = (o) => {
    // Ô nhập theo nhãn (antd Form.Item label[for]) hoặc CSS selector hoặc placeholder.
    const hienThiO = (el) => el && el.getClientRects().length > 0;
    const lopPhu = [...document.querySelectorAll('.ant-modal-wrap, .ant-drawer-content-wrapper')].filter(hienThi);
    const goc = lopPhu.length ? lopPhu[lopPhu.length - 1] : document;
    for (const g of [goc, document]) {
      try {
        const el = g.querySelector(o);
        if (el && hienThiO(el)) return el;
      } catch (e) { /* không phải selector */ }
      const nhan = [...g.querySelectorAll('label')].find((l) => chuan(l.innerText).replace(/[:*]\s*$/, '').trim() === o || l.getAttribute('title') === o);
      if (nhan) {
        const id = nhan.getAttribute('for');
        const el = id ? document.getElementById(id) : null;
        if (el) return el;
        const item = nhan.closest('.ant-form-item');
        const el2 = item && item.querySelector('input:not([type=hidden]), textarea');
        if (el2) return el2;
      }
      const ph = [...g.querySelectorAll('input, textarea')].find((el) => el.getAttribute('placeholder') === o && hienThiO(el));
      if (ph) return ph;
    }
    return null;
  };
  return true;
})()
"""


class TrinhDuyet:
    """Một Chrome headless + một tab, điều khiển qua CDP."""

    def __init__(self, base_url: str = "https://localhost", chrome: str | None = None,
                 rong: int = RONG, cao: int = CAO) -> None:
        self.base_url = base_url.rstrip("/")
        self.chrome = chrome or os.environ.get("CHROME", "/usr/bin/google-chrome")
        self.rong, self.cao = rong, cao
        self._proc: subprocess.Popen | None = None
        self._profile: str | None = None
        self._ws: Any = None
        self._id = 0
        self._cho: dict[int, asyncio.Future] = {}
        self._su_kien: dict[str, list[asyncio.Future]] = {}
        self._doc_task: asyncio.Task | None = None
        self._dang_tai: dict[str, float] = {}
        self.loi_js: list[str] = []
        self.loi_console: list[str] = []
        self.http_loi: list[dict] = []

    # ------------------------------------------------------------------ vòng đời
    async def __aenter__(self) -> "TrinhDuyet":
        try:
            await self._khoi_dong()
        except BaseException:
            await self.dong()
            raise
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.dong()

    async def _khoi_dong(self) -> None:
        self._profile = tempfile.mkdtemp(prefix="ntma-cdp-")
        args = [
            self.chrome, "--headless=new", "--remote-debugging-port=0",
            "--remote-debugging-address=127.0.0.1", f"--user-data-dir={self._profile}",
            "--ignore-certificate-errors", "--no-first-run", "--no-default-browser-check",
            "--hide-scrollbars", "--lang=vi-VN", f"--window-size={self.rong},{self.cao}",
            "--disable-gpu", "--disable-extensions", "--disable-background-networking",
            "--disable-sync", "--mute-audio", "about:blank",
        ]
        self._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      start_new_session=True)
        port_file = Path(self._profile) / "DevToolsActivePort"
        han = time.monotonic() + 20
        while not (port_file.exists() and port_file.read_text().strip()):
            if self._proc.poll() is not None:
                raise LoiTrinhDuyet(f"Chrome thoát ngay (mã {self._proc.returncode})")
            if time.monotonic() > han:
                raise LoiTrinhDuyet("Không đọc được DevToolsActivePort sau 20 s")
            await asyncio.sleep(0.1)
        port = int(port_file.read_text().splitlines()[0])
        ws_url = None
        for _ in range(50):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as r:
                muc = [t for t in json.load(r) if t.get("type") == "page"]
            if muc:
                ws_url = muc[0]["webSocketDebuggerUrl"]
                break
            await asyncio.sleep(0.1)
        if not ws_url:
            raise LoiTrinhDuyet("Không tìm thấy tab trang trong Chrome")
        self._ws = await websockets.connect(ws_url, max_size=64 * 1024 * 1024, ping_interval=None)
        self._doc_task = asyncio.create_task(self._doc())
        for dom in ("Page", "Runtime", "Network", "Log", "DOM"):
            await self.gui(f"{dom}.enable")
        await self.gui("Emulation.setDeviceMetricsOverride",
                       {"width": self.rong, "height": self.cao, "deviceScaleFactor": 1, "mobile": False})
        await self.gui("Page.addScriptToEvaluateOnNewDocument", {"source": _JS_TIM})
        # Headless không có cửa sổ được focus -> focus/blur (onBlur của React) không bắn nếu thiếu dòng này.
        await self.gui("Emulation.setFocusEmulationEnabled", {"enabled": True})

    async def dong(self) -> None:
        if self._doc_task:
            self._doc_task.cancel()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        if self._proc is not None and self._proc.poll() is None:
            try:
                os.killpg(self._proc.pid, 15)
            except (ProcessLookupError, PermissionError):
                self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self._proc.pid, 9)
                except ProcessLookupError:
                    pass
                self._proc.wait(timeout=5)
        if self._profile:
            shutil.rmtree(self._profile, ignore_errors=True)
        self._proc = self._ws = self._profile = None

    # ---------------------------------------------------------------- giao thức
    async def _doc(self) -> None:
        async for raw in self._ws:
            m = json.loads(raw)
            if "id" in m:
                fut = self._cho.pop(m["id"], None)
                if fut and not fut.done():
                    if "error" in m:
                        fut.set_exception(LoiTrinhDuyet(f"CDP lỗi: {m['error'].get('message')}"))
                    else:
                        fut.set_result(m.get("result", {}))
                continue
            self._xu_ly_su_kien(m.get("method", ""), m.get("params", {}))

    def _xu_ly_su_kien(self, method: str, p: dict) -> None:
        if method == "Runtime.exceptionThrown":
            d = p.get("exceptionDetails", {})
            self.loi_js.append((d.get("exception") or {}).get("description") or d.get("text", "exception"))
        elif method == "Runtime.consoleAPICalled" and p.get("type") == "error":
            self.loi_console.append(" ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", []))[:300])
        elif method == "Log.entryAdded":
            e = p.get("entry", {})
            # Lỗi tải tài nguyên (source network) đã được thu qua Network.responseReceived.
            if e.get("level") == "error" and e.get("source") != "network":
                self.loi_console.append(f"{e.get('source')}: {e.get('text', '')}"[:300])
        elif method == "Network.requestWillBeSent":
            self._dang_tai[p.get("requestId", "")] = time.monotonic()
        elif method in ("Network.loadingFinished", "Network.loadingFailed"):
            self._dang_tai.pop(p.get("requestId", ""), None)
        elif method == "Network.responseReceived":
            r = p.get("response", {})
            if r.get("status", 0) >= 400:
                url = r.get("url", "")
                duong_dan = "/" + url.split("://", 1)[-1].split("/", 1)[-1] if "://" in url else url
                self.http_loi.append({"url": duong_dan.split("?", 1)[0], "status": r["status"]})
        for fut in self._su_kien.pop(method, []):
            if not fut.done():
                fut.set_result(p)

    async def gui(self, method: str, params: dict | None = None, timeout: float = 30) -> dict:
        self._id += 1
        fut = asyncio.get_running_loop().create_future()
        self._cho[self._id] = fut
        await self._ws.send(json.dumps({"id": self._id, "method": method, "params": params or {}}))
        return await asyncio.wait_for(fut, timeout)

    def _doi_su_kien(self, method: str) -> asyncio.Future:
        fut = asyncio.get_running_loop().create_future()
        self._su_kien.setdefault(method, []).append(fut)
        return fut

    async def js(self, bieu_thuc: str, cho_promise: bool = False) -> Any:
        r = await self.gui("Runtime.evaluate", {"expression": bieu_thuc, "returnByValue": True,
                                                "awaitPromise": cho_promise})
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            raise LoiTrinhDuyet(f"JS lỗi: {(d.get('exception') or {}).get('description') or d.get('text')}")
        return r.get("result", {}).get("value")

    def xoa_bo_thu(self) -> None:
        self.loi_js.clear()
        self.loi_console.clear()
        self.http_loi.clear()

    # --------------------------------------------------------------- thao tác
    async def mo(self, path: str, timeout: float = 30) -> None:
        """Điều hướng tới base_url + path và chờ sự kiện load + mạng rảnh."""
        url = path if "://" in path else self.base_url + path
        tai = self._doi_su_kien("Page.loadEventFired")
        self._dang_tai.clear()  # request của trang cũ có thể không bao giờ báo xong
        await self.gui("Page.navigate", {"url": url})
        await asyncio.wait_for(tai, timeout)
        await self.js(_JS_TIM)
        await self.cho_on_dinh()

    async def cho_on_dinh(self, timeout: float = 20, yen: float = 0.5) -> None:
        """Chờ tới khi không còn request mạng nào và không còn spinner antd."""
        han = time.monotonic() + timeout
        yen_tu = None
        while time.monotonic() < han:
            quay = await self.js(
                "[...document.querySelectorAll('.ant-spin-spinning, .ant-skeleton-active, .ant-btn-loading')]"
                ".filter(e => e.getClientRects().length).length")
            # Request treo quá 8 s (vd. bị hủy mà không có loadingFailed) không tính.
            con = [t for t in self._dang_tai.values() if time.monotonic() - t < 8]
            if not con and not quay:
                yen_tu = yen_tu or time.monotonic()
                if time.monotonic() - yen_tu >= yen:
                    return
            else:
                yen_tu = None
            await asyncio.sleep(0.1)
        # Hết giờ không phải lỗi cứng (vd. long-poll); bước sẽ kiểm tra chữ mong đợi.

    async def cho_chu(self, chu: str, timeout: float = 15) -> None:
        han = time.monotonic() + timeout
        can = json.dumps(chu, ensure_ascii=False)
        while time.monotonic() < han:
            if await self.js(f"document.body && document.body.innerText.replace(/\\s+/g,' ').includes({can})"):
                return
            await asyncio.sleep(0.2)
        raise LoiTrinhDuyet(f"Không thấy chữ {chu!r} sau {timeout:g} s")

    async def cho_het_chu(self, chu: str, timeout: float = 15) -> None:
        han = time.monotonic() + timeout
        can = json.dumps(chu, ensure_ascii=False)
        while time.monotonic() < han:
            if not await self.js(f"document.body.innerText.replace(/\\s+/g,' ').includes({can})"):
                return
            await asyncio.sleep(0.2)
        raise LoiTrinhDuyet(f"Chữ {chu!r} vẫn còn sau {timeout:g} s")

    async def dang_nhap(self, ma: str, mat_khau: str) -> None:
        """Đăng nhập bằng fetch trong trang (đặt cookie refresh httpOnly), rồi mở /tong-quan."""
        await self.gui("Network.clearBrowserCookies")
        await self.mo("/dang-nhap")
        than = json.dumps({"dang_nhap": ma, "mat_khau": mat_khau}, ensure_ascii=False)
        ma_http = await self.js(
            "fetch('/api/auth/login', {method: 'POST', credentials: 'include', "
            "headers: {'Content-Type': 'application/json'}, body: " + json.dumps(than) + "})"
            ".then(r => r.status)", cho_promise=True)
        if ma_http != 200:
            raise LoiTrinhDuyet(f"Đăng nhập {ma} trả HTTP {ma_http}")
        await self.mo("/tong-quan")
        await self.cho_chu("Đăng xuất", 20)
        await self.cho_on_dinh()
        # Lỗi 401 của /api/auth/refresh khi chưa có phiên là hành vi đúng, không tính.
        self.xoa_bo_thu()

    async def _tam_phan_tu(self, muc: str, pham_vi: str | None = None, hang: str | None = None,
                           timeout: float = 10) -> dict:
        han = time.monotonic() + timeout
        args = ", ".join(json.dumps(x, ensure_ascii=False) for x in (muc, pham_vi, hang))
        while True:
            r = await self.js(
                f"(() => {{ const el = window.__ntmaTim({args}); if (!el) return null;"
                " el.scrollIntoView({block: 'center', inline: 'center'});"
                " const r = el.getBoundingClientRect();"
                " return {x: r.left + r.width / 2, y: r.top + r.height / 2}; })()")
            if r:
                return r
            if time.monotonic() > han:
                raise LoiTrinhDuyet(f"Không thấy phần tử {muc!r}" + (f" trong {pham_vi!r}" if pham_vi else "")
                                    + (f" ở hàng {hang!r}" if hang else ""))
            await asyncio.sleep(0.2)

    async def bam(self, muc: str, pham_vi: str | None = None, hang: str | None = None,
                  timeout: float = 10) -> None:
        """Bấm chuột thật (Input.dispatchMouseEvent) vào tâm phần tử khớp chữ/selector."""
        await asyncio.sleep(0.05)
        vt = await self._tam_phan_tu(muc, pham_vi, hang, timeout)
        await asyncio.sleep(0.05)
        vt = await self._tam_phan_tu(muc, pham_vi, hang, timeout)  # sau khi cuộn đã ổn định
        x, y = vt["x"], vt["y"]
        await self.gui("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
        for loai in ("mousePressed", "mouseReleased"):
            await self.gui("Input.dispatchMouseEvent",
                           {"type": loai, "x": x, "y": y, "button": "left", "clickCount": 1})

    async def go(self, o: str, chu: str, timeout: float = 10) -> None:
        """Điền chữ vào ô (nhãn / selector / placeholder). Với antd Select: mở, gõ, chọn option."""
        han = time.monotonic() + timeout
        muc = json.dumps(o, ensure_ascii=False)
        while True:
            loai = await self.js(
                f"(() => {{ const el = window.__ntmaO({muc}); if (!el) return null;"
                " window.__ntmaDich = el; el.scrollIntoView({block: 'center'});"
                " return el.closest('.ant-select') ? 'select' : (el.closest('.ant-picker') ? 'picker' : el.tagName); })()")
            if loai:
                break
            if time.monotonic() > han:
                raise LoiTrinhDuyet(f"Không thấy ô {o!r}")
            await asyncio.sleep(0.2)
        if loai == "select":
            vt = await self.js("(() => { const s = window.__ntmaDich.closest('.ant-select');"
                               " const r = s.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2}; })()")
            for t in ("mousePressed", "mouseReleased"):
                await self.gui("Input.dispatchMouseEvent",
                               {"type": t, "x": vt["x"], "y": vt["y"], "button": "left", "clickCount": 1})
            await asyncio.sleep(0.2)
            tim_duoc = await self.js("(() => { const s = window.__ntmaDich.closest('.ant-select');"
                                     " return s.classList.contains('ant-select-show-search'); })()")
            if tim_duoc:
                await self.js("window.__ntmaDich.focus()")
                await self.gui("Input.insertText", {"text": chu})
                await asyncio.sleep(0.3)
            await self.bam(chu, ".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
            await asyncio.sleep(0.2)
            return
        if loai == "picker":
            await self.js("window.__ntmaDich.focus()")
            await self.gui("Input.insertText", {"text": chu})
            await self.gui("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter",
                                                      "windowsVirtualKeyCode": 13})
            await self.gui("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter",
                                                      "windowsVirtualKeyCode": 13})
            return
        gia_tri = json.dumps(chu, ensure_ascii=False)
        await self.js(
            "(() => { const el = window.__ntmaDich; el.focus();"
            " const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;"
            " Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, " + gia_tri + ");"
            " el.dispatchEvent(new Event('input', {bubbles: true}));"
            " el.dispatchEvent(new Event('change', {bubbles: true})); el.blur(); })()")

    async def tai_len(self, selector: str, duong_dan: str) -> None:
        """Gắn tệp vào <input type=file> (DOM.setFileInputFiles, đường dẫn tuyệt đối)."""
        p = str(Path(duong_dan).resolve())
        if not Path(p).is_file():
            raise LoiTrinhDuyet(f"Không thấy tệp để tải lên: {p}")
        goc = await self.gui("DOM.getDocument", {"depth": 0})
        node = await self.gui("DOM.querySelector", {"nodeId": goc["root"]["nodeId"], "selector": selector})
        if not node.get("nodeId"):
            raise LoiTrinhDuyet(f"Không thấy ô tải tệp {selector!r}")
        await self.gui("DOM.setFileInputFiles", {"files": [p], "nodeId": node["nodeId"]})

    async def chup(self, duong_dan: str, full_page: bool = False) -> None:
        """Chụp màn hình PNG (mặc định đúng khung nhìn rong x cao)."""
        tham_so: dict[str, Any] = {"format": "png", "captureBeyondViewport": False}
        if full_page:
            cao = await self.js("Math.ceil(document.documentElement.scrollHeight)")
            tham_so["clip"] = {"x": 0, "y": 0, "width": self.rong, "height": cao, "scale": 1}
            tham_so["captureBeyondViewport"] = True
        r = await self.gui("Page.captureScreenshot", tham_so)
        Path(duong_dan).parent.mkdir(parents=True, exist_ok=True)
        Path(duong_dan).write_bytes(base64.b64decode(r["data"]))

    async def cuon(self, muc: str | int, pham_vi: str | None = None) -> None:
        """Cuộn tới phần tử (đặt ở đầu khung nhìn) hoặc tới tọa độ y (số)."""
        if isinstance(muc, int):
            await self.js(f"window.scrollTo(0, {muc})")
        else:
            await self._tam_phan_tu(muc, pham_vi)
            await self.js("(() => { const el = window.__ntmaTim(" + json.dumps(muc, ensure_ascii=False) + ", "
                          + json.dumps(pham_vi) + ", null); el && el.scrollIntoView({block: 'start'});"
                          " window.scrollBy(0, -80); })()")
        await asyncio.sleep(0.3)

    async def phim(self, key: str) -> None:
        """Nhấn một phím (vd. Escape để đóng dropdown)."""
        ma = {"Escape": 27, "Enter": 13, "Tab": 9}.get(key, 0)
        for t in ("keyDown", "keyUp"):
            await self.gui("Input.dispatchKeyEvent", {"type": t, "key": key, "code": key,
                                                      "windowsVirtualKeyCode": ma})

    async def do_rong(self) -> int:
        """document.documentElement.scrollWidth (NFR-16: <= chiều rộng khung nhìn)."""
        return int(await self.js("document.documentElement.scrollWidth"))
