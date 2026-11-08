"""
上传文件实际内容校验（魔术字节 / 轻量结构解析）。

不依赖客户端 Content-Type；不引入第三方文件识别库。
扩展名仍须在调用方白名单内；本模块校验「扩展名 ↔ 内容」一致性。
"""

from __future__ import annotations

import zipfile
from pathlib import Path


class FileContentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# OLE Compound File Binary（旧版 doc / xls / ppt）
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

def _u16(name: str) -> bytes:
    """OLE 目录项名为 UTF-16LE。"""
    return name.encode("utf-16-le")


# 各扩展名在 OLE 目录中常见的流名（UTF-16LE）；兼查 ASCII 兜底
_OLE_STREAM_HINTS: dict[str, tuple[bytes, ...]] = {
    "doc": (_u16("WordDocument"), b"WordDocument"),
    "xls": (_u16("Workbook"), _u16("Book"), b"Workbook", b"Book"),
    "ppt": (
        _u16("PowerPoint Document"),
        _u16("Current User"),
        b"PowerPoint Document",
        b"Current User",
    ),
}

_OOXML_REQUIRED_PREFIX: dict[str, str] = {
    "docx": "word/",
    "xlsx": "xl/",
    "pptx": "ppt/",
}


def _ext_of(filename: str) -> str:
    name = Path(filename).name
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


def _read_head(path: Path, n: int = 65536) -> bytes:
    with path.open("rb") as f:
        return f.read(n)


def _assert_pdf_bytes(data: bytes) -> None:
    if not data.startswith(b"%PDF"):
        raise FileContentError("文件内容与扩展名不符：不是有效的 PDF")
    # 损坏/截断：缺少 EOF 标记
    if b"%%EOF" not in data and b"%%eof" not in data:
        # 大文件只读了头部时可能看不到 EOF；调用方对大文件应传完整或另行处理
        # 此处约定：传入的 data 应覆盖全文件，或至少覆盖末尾（见 validate_pdf_file）
        raise FileContentError("PDF 文件损坏或不完整")


def validate_pdf_bytes(data: bytes, *, require_eof: bool = True) -> None:
    """校验内存中的 PDF 字节。空内容单独拒绝。"""
    if not data or not data.strip():
        raise FileContentError("空 PDF 不允许解析")
    if not data.startswith(b"%PDF"):
        raise FileContentError("文件内容与扩展名不符：不是有效的 PDF")
    if require_eof and b"%%EOF" not in data and b"%%eof" not in data:
        raise FileContentError("PDF 文件损坏或不完整")
    # 仅有头部、几乎无对象体
    if len(data) < 40:
        raise FileContentError("PDF 内容为空或无效")


def validate_pdf_file(path: Path) -> None:
    """读取完整小文件或头尾拼接校验 PDF。"""
    size = path.stat().st_size
    if size == 0:
        raise FileContentError("空文件不允许上传")
    with path.open("rb") as f:
        head = f.read(16)
        if not head.startswith(b"%PDF"):
            raise FileContentError("文件内容与扩展名不符：不是有效的 PDF")
        if size < 40:
            raise FileContentError("PDF 内容为空或无效")
        if size <= 65536:
            rest = f.read()
            data = head + rest
        else:
            f.seek(max(0, size - 1024))
            tail = f.read()
            data = head + tail
    if b"%%EOF" not in data and b"%%eof" not in data:
        raise FileContentError("PDF 文件损坏或不完整")


def _validate_ole(path: Path, ext: str) -> None:
    head = _read_head(path, 8192)
    if not head.startswith(_OLE_MAGIC):
        raise FileContentError(f"文件内容与扩展名不符：不是有效的 {ext.upper()}（OLE）文件")
    # 再扫更大一段以匹配流名（旧版 Office）
    blob = head
    if path.stat().st_size > len(head):
        with path.open("rb") as f:
            blob = f.read(min(path.stat().st_size, 512 * 1024))
    hints = _OLE_STREAM_HINTS.get(ext, ())
    if hints and not any(h in blob for h in hints):
        # 保守：有 OLE 魔数但完全不像对应应用 → 拒绝伪装
        raise FileContentError(f"文件内容与扩展名不符：不是有效的 {ext.upper()} 文档")


def _validate_ooxml(path: Path, ext: str) -> None:
    prefix = _OOXML_REQUIRED_PREFIX[ext]
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
    except zipfile.BadZipFile as exc:
        raise FileContentError(
            f"文件内容与扩展名不符：不是有效的 {ext.upper()}（OOXML）文件"
        ) from exc
    if not any(n.startswith(prefix) for n in names):
        raise FileContentError(f"文件内容与扩展名不符：缺少 {ext.upper()} 必要结构")
    if "[Content_Types].xml" not in names and not any(
        n.endswith("[Content_Types].xml") for n in names
    ):
        raise FileContentError(f"文件内容与扩展名不符：不是有效的 {ext.upper()} 包")


def _validate_png(data: bytes) -> None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise FileContentError("文件内容与扩展名不符：不是有效的 PNG")


def _validate_jpeg(data: bytes) -> None:
    if not (len(data) >= 3 and data[0:3] == b"\xff\xd8\xff"):
        raise FileContentError("文件内容与扩展名不符：不是有效的 JPEG")


def _validate_ftyp_media(data: bytes, ext: str) -> None:
    # ISO BMFF: size(4) + 'ftyp'(4) at offset 4
    if len(data) < 12 or data[4:8] != b"ftyp":
        raise FileContentError(f"文件内容与扩展名不符：不是有效的 {ext.upper()} 媒体文件")


def validate_upload_content(path: Path, original_filename: str) -> None:
    """
    按原始文件名扩展名校验落盘前临时文件内容。
    失败抛 FileContentError(status_code=400)。
    """
    if not path.is_file():
        raise FileContentError("上传临时文件缺失", status_code=500)

    ext = _ext_of(original_filename)
    if not ext:
        raise FileContentError("无法识别文件扩展名")

    size = path.stat().st_size
    if size == 0:
        raise FileContentError("空文件不允许上传")

    if ext == "pdf":
        validate_pdf_file(path)
        return

    if ext in ("docx", "xlsx", "pptx"):
        _validate_ooxml(path, ext)
        return

    if ext in ("doc", "xls", "ppt"):
        _validate_ole(path, ext)
        return

    head = _read_head(path, 64)

    if ext == "png":
        _validate_png(head)
        return
    if ext in ("jpg", "jpeg"):
        _validate_jpeg(head)
        return
    if ext in ("mp4", "mov"):
        _validate_ftyp_media(head, ext)
        return

    raise FileContentError(f"未配置内容校验规则的扩展名：{ext}")
