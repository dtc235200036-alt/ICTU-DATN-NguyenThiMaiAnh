"""Sinh file PDF có chữ ký số PKCS#7 (chứng thư tự ký) cho kiểm thử luồng Lãnh
đạo bộ môn phê duyệt đề cương — cùng cấu trúc /ByteRange + /Contents mà các
công cụ ký số (Adobe, VNPT-CA, ...) nhúng vào PDF."""
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import NameOID

_PLACEHOLDER_RANGE = b"[0 0000000000 0000000000 0000000000]"
_CONTENTS_HEX_LEN = 16384


def _self_signed(common_name: str):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    return cert, key


def sign_pdf(base_pdf: bytes, signer: str = "Lãnh đạo Bộ môn CNTT") -> bytes:
    """Thêm một trường chữ ký phủ toàn bộ file vào cuối `base_pdf`."""
    cert, key = _self_signed(signer)
    sig_obj = (
        b"\n999 0 obj\n<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /adbe.pkcs7.detached"
        b" /M (D:20261018093000+07'00') /ByteRange " + _PLACEHOLDER_RANGE
        + b" /Contents <" + b"0" * _CONTENTS_HEX_LEN + b"> >>\nendobj\n"
    )
    data = base_pdf + sig_obj
    start = data.rindex(b"/Contents <") + len(b"/Contents ")
    end = data.index(b">", start) + 1
    byte_range = b"[0 %010d %010d %010d]" % (start, end, len(data) - end)
    data = data.replace(_PLACEHOLDER_RANGE, byte_range, 1)

    signed_part = data[:start] + data[end:]
    signature = (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(signed_part)
        .add_signer(cert, key, hashes.SHA256())
        .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
    )
    hex_sig = signature.hex().encode().ljust(_CONTENTS_HEX_LEN, b"0")
    assert len(hex_sig) == _CONTENTS_HEX_LEN
    return data[: start + 1] + hex_sig + data[end - 1 :]
