from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("architecture-diagram.png")
W, H = 2400, 1470


def load_font(name: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_dir = Path("C:/Windows/Fonts")
    candidates = [
        font_dir / name,
        font_dir / ("arialbd.ttf" if bold else "arial.ttf"),
        font_dir / ("segoeuib.ttf" if bold else "segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), "#F8FAFC")
d = ImageDraw.Draw(img)

f_title = load_font("arialbd.ttf", 62, True)
f_sub = load_font("arial.ttf", 31)
f_section = load_font("arialbd.ttf", 39, True)
f_node = load_font("arialbd.ttf", 30, True)
f_body = load_font("arial.ttf", 24)
f_small = load_font("arial.ttf", 21)
f_label = load_font("arialbd.ttf", 23, True)

INK = "#0B2545"
MUTED = "#475467"
BLUE = "#2E74B5"
DARK_BLUE = "#1F4D78"
GREEN = "#178A45"
BORDER = "#D0D5DD"
WHITE = "#FFFFFF"


def shadow_box(x: int, y: int, w: int, h: int, r: int = 32, fill: str = WHITE) -> None:
    for index, color in enumerate(["#E2E8F0", "#E8EEF5", "#EEF2F7"]):
        offset = 10 + index * 4
        d.rounded_rectangle((x, y + offset, x + w, y + h + offset), radius=r, fill=color)
    d.rounded_rectangle((x, y, x + w, y + h), radius=r, fill=fill, outline=BORDER, width=3)


def text_box(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    lines: list[str],
    fill: str = WHITE,
    accent: str | None = None,
) -> None:
    shadow_box(x, y, w, h, 26, fill)
    if accent:
        d.rounded_rectangle((x, y, x + 18, y + h), radius=20, fill=accent)
    d.text((x + 42, y + 32), title, font=f_node, fill=INK)
    yy = y + 78
    for line in lines:
        d.text((x + 42, yy), line, font=f_small if len(line) > 34 else f_body, fill=MUTED)
        yy += 31


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = BLUE, width: int = 6) -> None:
    d.line((x1, y1, x2, y2), fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 24
    points = [
        (x2, y2),
        (x2 - size * math.cos(angle - math.pi / 6), y2 - size * math.sin(angle - math.pi / 6)),
        (x2 - size * math.cos(angle + math.pi / 6), y2 - size * math.sin(angle + math.pi / 6)),
    ]
    d.polygon(points, fill=color)


def section_panel(x: int, y: int, w: int, h: int, title: str, subtitle: str, fill: str) -> None:
    shadow_box(x, y, w, h, 44, fill)
    d.text((x + 46, y + 42), title, font=f_section, fill=INK)
    d.text((x + 46, y + 91), subtitle, font=f_body, fill=MUTED)


def inner_box(x: int, y: int, w: int, h: int, title: str, subtitle: str) -> None:
    d.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=WHITE, outline=BORDER, width=2)
    d.text((x + 28, y + 29), title, font=f_node, fill=INK)
    d.text((x + 28, y + 70), subtitle, font=f_small, fill=MUTED)


d.ellipse((2080, -130, 2600, 390), fill="#DBEAFE")
d.ellipse((-190, 1060, 520, 1770), fill="#DCFCE7")

d.text((120, 78), "Sơ Đồ Kiến Trúc Hệ Thống BT01", font=f_title, fill=INK)
d.text(
    (123, 137),
    "Phân tích log web quy mô lớn với HDFS, MapReduce, YARN, Python Streaming, PostgreSQL và Grafana",
    font=f_sub,
    fill=MUTED,
)

text_box(
    120,
    240,
    390,
    150,
    "Log Generator",
    ["Python sinh 2.000.000 dòng", "Apache Combined Log Format"],
    accent=BLUE,
)

section_panel(
    330,
    470,
    650,
    555,
    "HDFS - Lưu trữ phân tán",
    "Tổ chức log theo thư mục ngày: /logs/yyyy/MM/dd/",
    "#EAF2FF",
)
inner_box(390, 645, 240, 132, "NameNode", "Quản lý metadata")
inner_box(690, 645, 230, 132, "DataNode 1", "Lưu block dữ liệu")
inner_box(690, 825, 230, 132, "DataNode 2", "Lưu block dữ liệu")
inner_box(390, 825, 240, 132, "Raw Logs", "access.log theo ngày")

section_panel(
    1080,
    470,
    635,
    555,
    "YARN + MapReduce",
    "Hadoop Streaming chạy mapper/reducer Python",
    "#F0FBF2",
)
inner_box(1140, 645, 255, 132, "ResourceManager", "Điều phối job")
inner_box(1450, 645, 205, 132, "Mapper", "parse / emit")
inner_box(1140, 825, 255, 132, "NodeManager", "task container")
inner_box(1450, 825, 205, 132, "Reducer", "sum / top-N")

text_box(
    1165,
    1120,
    520,
    150,
    "HDFS Output",
    ["/bt01/output/normalized", "/bt01/output/top_ips, status, URL, hour"],
    accent=GREEN,
)

section_panel(1815, 470, 400, 555, "Dashboard", "Trực quan hóa tương tác", "#FFF9E8")
inner_box(1872, 660, 285, 120, "PostgreSQL", "Load TSV export")
inner_box(1872, 840, 285, 120, "Grafana", "Filter ngày / giờ")

arrow(510, 315, 510, 470)
d.text((555, 397), "01. Nạp log lên HDFS", font=f_label, fill=BLUE)
arrow(980, 748, 1080, 748)
d.text((940, 700), "02. Đọc input", font=f_label, fill=BLUE)
arrow(1400, 1025, 1400, 1120)
d.text((1435, 1085), "03. Ghi kết quả", font=f_label, fill=BLUE)
arrow(1685, 1190, 1872, 720)
d.text((1700, 1135), "04. Export TSV & load DB", font=f_label, fill=BLUE)
arrow(2015, 780, 2015, 840)
d.text((2040, 815), "05. Query", font=f_label, fill=BLUE)

shadow_box(120, 1160, 860, 170, 34, WHITE)
d.text((170, 1207), "Các chương trình phân tích chính", font=f_node, fill=INK)
d.text((170, 1260), "1. Top 20 IP truy cập nhiều nhất  ·  2. Mã HTTP theo ngày", font=f_body, fill=MUTED)
d.text((170, 1298), "3. Top 10 URL mỗi ngày  ·  4. Lưu lượng theo 24 giờ", font=f_body, fill=MUTED)

shadow_box(1770, 230, 445, 118, 28, WHITE)
d.text((1815, 262), "Web UI theo dõi", font=f_label, fill=DARK_BLUE)
d.text((1815, 300), "HDFS UI: localhost:9871", font=f_small, fill=MUTED)
d.text((1815, 329), "YARN UI: localhost:8089", font=f_small, fill=MUTED)

d.line((120, 1382, 2280, 1382), fill=BORDER, width=3)
d.text(
    (120, 1405),
    "Ảnh 1 - Sơ đồ kiến trúc hệ thống BT01. Có thể chèn trực tiếp vào báo cáo hoặc import SVG vào Figma.",
    font=f_small,
    fill="#667085",
)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, quality=95)
print(OUT.name)
