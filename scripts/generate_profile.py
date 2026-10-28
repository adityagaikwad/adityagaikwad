#!/usr/bin/env python3
"""Generate the single, self-contained SVG used by the GitHub profile README."""

from pathlib import Path
import html
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "icons"
OUT = ROOT / "assets" / "readme.svg"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

WIDTH = 850
PAD = 24
BG = "#0a0a0a"
INK = "#ededed"
MID = "#a3a3a3"
DIM = "#5f5f5f"
RULE = "#2a2a2a"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
BLINK = '<animate attributeName="opacity" values="1;0" keyTimes="0;.5" calcMode="discrete" dur="1.1s" repeatCount="indefinite"/>'

FONT = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#", "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.####", "I": "###|.#.|.#.|.#.|.#.|.#.|###",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#", "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#.",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..", " ": "...|...|...|...|...|...|...",
}
FONT = {key: value.split("|") for key, value in FONT.items()}

PROGRAMMING = [("python", "Python"), ("javascript", "JavaScript"), ("typescript", "TypeScript"),
               ("java", "Java"), ("c", "C"), ("rust", "Rust"), ("go", "Go")]
TOOLS = [("nodejs", "Node.js"), ("angular", "Angular"), ("express", "Express"), ("terraform", "Terraform"),
         ("terragrunt", "Terragrunt"), ("kubernetes", "Kubernetes"), ("docker", "Docker"), ("graphql", "GraphQL"),
         ("jenkins", "Jenkins"), ("apachekafka", "Apache Kafka"), ("elasticsearch", "Elasticsearch"),
         ("apachespark", "Apache Spark"), ("apachehadoop", "Apache Hadoop"), ("amazonaws", "Amazon Web Services"),
         ("googlecloud", "Google Cloud Platform"), ("tensorflow", "TensorFlow"), ("keras", "Keras"), ("numpy", "NumPy")]
DATABASES = [("mysql", "MySQL"), ("redis", "Redis"), ("mongodb", "MongoDB"),
             ("clickhouse", "ClickHouse"), ("postgresql", "PostgreSQL")]


def glyph(char):
    return FONT.get(char, FONT[" "])


def pixel_width(text, scale):
    return (sum(len(glyph(char)[0]) + 1 for char in text) - 1) * scale


def pixel_path(text, x, y, scale):
    paths = []
    cursor = x
    for char in text:
        rows = glyph(char)
        for row_idx, row in enumerate(rows):
            col = 0
            while col < len(row):
                if row[col] != "#":
                    col += 1
                    continue
                end = col
                while end < len(row) and row[end] == "#":
                    end += 1
                paths.append(f"M{cursor + col * scale} {y + row_idx * scale}h{(end-col)*scale}v{scale}h{-((end-col)*scale)}z")
                col = end
        cursor += (len(rows[0]) + 1) * scale
    return "".join(paths)


def pixel_name(text, x, y, scale):
    path = pixel_path(text, x, y, scale)
    return (f'<path fill="#4d4d4d" transform="translate({scale} {scale})" d="{path}"/>'
            f'<path fill="{INK}" d="{path}"/>')


def text(x, y, value, size=12, color=INK, weight=400, anchor=None):
    attrs = f' x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{color}"'
    if weight != 400:
        attrs += f' font-weight="{weight}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f"<text{attrs}>{html.escape(value)}</text>"


def rewrite_icon(icon_id, x, y, size):
    root = ET.parse(ICONS / f"{icon_id}.svg").getroot()
    view_box = root.attrib.get("viewBox", "0 0 128 128").replace(",", " ").split()
    vx, vy, vw, vh = map(float, view_box)
    scale = size / max(vw, vh)
    prefix = f"i{icon_id}-"
    id_map = {element.attrib["id"]: prefix + element.attrib["id"] for element in root.iter() if "id" in element.attrib}
    for element in root.iter():
        if "id" in element.attrib:
            element.set("id", id_map[element.attrib["id"]])
        for key, value in list(element.attrib.items()):
            for old, new in id_map.items():
                value = value.replace(f"url(#{old})", f"url(#{new})").replace(f"#{old}", f"#{new}")
            if icon_id in {"rust", "express", "apachekafka"}:
                if key == "fill" and value.lower() in {"#000", "#000000", "#231f20", "#231f20"}:
                    value = INK
            element.set(key, value)
    root_fill = root.attrib.get("fill")
    if icon_id in {"rust", "express"}:
        root_fill = INK
    fragments = "".join(ET.tostring(child, encoding="unicode") for child in list(root))
    root_attrs = ""
    if root_fill:
        root_attrs = f' fill="{root_fill}"'
    return (f'<g transform="translate({x} {y}) scale({scale}) translate({-vx} {-vy})"{root_attrs} '
            f'role="img" aria-label="{html.escape(next((name for key, name in PROGRAMMING+TOOLS+DATABASES if key==icon_id), icon_id))}">'
            f'<title>{html.escape(next((name for key, name in PROGRAMMING+TOOLS+DATABASES if key==icon_id), icon_id))}</title>'
            f'{fragments}</g>')


def icon_row(items, y, size=32, gap=16, x=PAD):
    parts = []
    for icon_id, name in items:
        parts.append(rewrite_icon(icon_id, x, y, size))
        x += size + gap
    return "".join(parts)


def stack_section():
    parts = [text(PAD, 24, "STACK", 12, MID), text(78, 24, "· 30 resume-backed technologies", 12, DIM)]
    parts.extend([text(PAD, 52, "PROGRAMMING LANGUAGES", 11, MID), icon_row(PROGRAMMING, 64)])
    parts.extend([text(PAD, 121, "FRAMEWORKS AND TOOLS", 11, MID), icon_row(TOOLS[:9], 133), icon_row(TOOLS[9:], 177)])
    parts.extend([text(PAD, 234, "DATABASES", 11, MID), icon_row(DATABASES, 246)])
    return 291, "".join(parts)


def card():
    name = "ADITYA GAIKWAD"
    scale = 6
    while pixel_width(name, scale) + 4 * scale > WIDTH - 2 * PAD and scale > 3:
        scale -= 1
    x_name, y_name = PAD, 60
    cursor_x = x_name + pixel_width(name, scale) + 2 * scale
    header_height = 130
    stack_height, stack = stack_section()
    detail_height = 178
    systems_height = 188
    footer_height = 40
    sections = []
    sections.append((header_height, "".join([
        text(PAD, 23, "adityagaikwad", 13, INK, 700), text(WIDTH-PAD, 23, "~/readme", 13, DIM, anchor="end"),
        f'<line x1="0" x2="{WIDTH}" y1="36.5" y2="36.5" stroke="{RULE}" stroke-dasharray="4 3"/>',
        text(PAD, 60, "WHOAMI", 12, MID), text(94, 60, "· SDE II / AI × Infrastructure", 12, DIM),
        pixel_name(name, x_name, y_name, scale), f'<rect x="{cursor_x}" y="{y_name}" width="{3*scale}" height="{7*scale}" fill="{INK}">{BLINK}</rect>',
        text(PAD, 130, "I build dependable systems where AI meets infrastructure.", 15, MID),
        text(PAD, 157, "Currently: Catalog ingestion reliability and AI-assisted diagnostics.", 12, DIM),
    ])))
    sections.append((stack_height, stack))
    sections.append((detail_height, "".join([
        text(PAD, 25, "ENGINEERING MODE", 12, MID), text(PAD, 55, "AI-assisted, not AI-replaced.", 12, DIM),
        text(PAD, 88, "structured inputs  ·  deterministic tooling", 14, INK), text(PAD, 116, "tracing  ·  evaluation harnesses", 14, INK),
        f'<line x1="425" y1="0" x2="425" y2="{detail_height}" stroke="{RULE}" stroke-dasharray="4 3"/>',
        text(449, 25, "PROFILE", 12, MID), text(449, 55, "CURRENT ROLE", 12, DIM), text(449, 79, "SDE II @ Amazon", 14, INK),
        text(449, 109, "BACKGROUND", 12, DIM), text(449, 133, "Senior Engineer @ Meta · VMware / Broadcom", 14, INK),
    ])))
    sections.append((systems_height, "".join([
        text(PAD, 25, "SYSTEMS LOG", 12, MID), text(120, 25, "· Work I Am Proud Of", 12, DIM),
        f'<rect x="{PAD}" y="44" width="5" height="5" fill="{INK}"/>', text(42, 51, "Amazon Catalog Contribution Pipeline", 14, INK),
        text(42, 72, "Data-consistency gates for high-volume catalog publishing", 12, DIM),
        f'<rect x="{PAD}" y="100" width="5" height="5" fill="{INK}"/>', text(42, 107, "AI Diagnostic Knowledge Graph", 14, INK),
        text(42, 128, "Expanding diagnostic coverage across an ingestion pipeline", 12, DIM),
        f'<rect x="{PAD}" y="156" width="5" height="5" fill="{INK}"/>', text(42, 163, "Agentic Infrastructure And Data Tooling", 14, INK),
        text(42, 184, "Meta, VMware, And Broadcom systems work", 12, DIM),
    ])))
    sections.append((footer_height, "".join([
        text(PAD, 24, "Pinned repositories below are the public workbench", 11, DIM),
        text(WIDTH-PAD, 24, "linkedin.com/in/aditya-gaikwad", 11, DIM, anchor="end"),
    ])))

    content, y = [], 0
    for index, (height, markup) in enumerate(sections):
        if index:
            content.append(f'<line x1="0" x2="{WIDTH}" y1="{y+0.5}" y2="{y+0.5}" stroke="{RULE}" stroke-dasharray="4 3"/>')
        content.append(f'<g transform="translate(0 {y})">{markup}</g>')
        y += height
    return (f'<svg xmlns="{SVG_NS}" width="{WIDTH}" height="{y}" viewBox="0 0 {WIDTH} {y}" role="img" aria-labelledby="title desc">'
            '<title id="title">Aditya Gaikwad engineering profile</title>'
            '<desc id="desc">Terminal-style profile with a pixel name, blinking cursor, resume-backed technology stack, and engineering experience.</desc>'
            f'<rect width="{WIDTH}" height="{y}" fill="{BG}"/>{"".join(content)}'
            f'<rect x=".5" y=".5" width="{WIDTH-1}" height="{y-1}" fill="none" stroke="#262626"/></svg>')


if __name__ == "__main__":
    OUT.write_text(card(), encoding="utf-8")
