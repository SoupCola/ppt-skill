#!/usr/bin/env python3
"""
ppt-builder — SVG 文字溢出/越界 lint(宽度预算法)

Stage 3 质量门:逐页 SVG 生成后立即运行,基于「文字宽度预算公式」做几何检查,
在导出 PPTX 之前抓出:文字溢出卡片、越出画布、文字互相重叠、悬空连线端点。

宽度预算与 svg-page-prompt.md 共享规则一致:
    中文/全角 ≈ 1.0 × font-size
    英文/数字/半角 ≈ 0.55 × font-size
    空格 ≈ 0.3 × font-size

用法:
    python scripts/svg_text_lint.py <svg文件或目录> [--tolerance 4] [--format ppt169]

输出:
    每条违规一行: [级别] 文件 — 类型: 描述
    退出码: 0 = 无违规, 1 = 有 error, 2 = 只有 warning
"""

import sys
import argparse
import math
from pathlib import Path
from xml.etree import ElementTree as ET

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'


def is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or
            0xFF01 <= o <= 0xFF60 or 0x3000 <= o <= 0x303F or
            0x2018 <= o <= 0x201D)  # 含全角标点与中文弯引号


def char_width(ch: str, size: float) -> float:
    if ch == ' ':
        return 0.3 * size
    if is_cjk(ch):
        return 1.0 * size
    return 0.55 * size


def est_width(s: str, size: float) -> float:
    return sum(char_width(c, size) for c in s)


def f(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def collect_graphics(root):
    """收集 rect 容器、line/polyline 连线与 polygon(箭头)包围盒(忽略 transform,规范本就禁嵌套 transform)。"""
    rects, segments, polys = [], [], []
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag == 'rect':
            x, y = f(el.get('x')), f(el.get('y'))
            w, h = f(el.get('width')), f(el.get('height'))
            if w > 0 and h > 0:
                fill = (el.get('fill') or 'none').lower()
                rects.append({'x': x, 'y': y, 'w': w, 'h': h,
                              'fill': fill, 'el': el})
        elif tag == 'line':
            segments.append(((f(el.get('x1')), f(el.get('y1'))),
                             (f(el.get('x2')), f(el.get('y2')))))
        elif tag == 'polyline':
            pts = (el.get('points') or '').replace(',', ' ').split()
            coords = [(f(pts[i]), f(pts[i + 1])) for i in range(0, len(pts) - 1, 2)]
            if len(coords) >= 2:
                segments.append(('polyline', coords))
        elif tag == 'polygon':
            pts = (el.get('points') or '').replace(',', ' ').split()
            coords = [(f(pts[i]), f(pts[i + 1])) for i in range(0, len(pts) - 1, 2)]
            if coords:
                xs, ys = [c[0] for c in coords], [c[1] for c in coords]
                polys.append((min(xs), min(ys), max(xs), max(ys)))
    return rects, segments, polys


def text_lines(text_el):
    """把 <text> 拆成若干逻辑行(处理 tspan x/dy)。返回 [(字符串, x, y, size, anchor, elem)]"""
    size = f(text_el.get('font-size'), 16.0)
    anchor = text_el.get('text-anchor') or 'start'
    x0, y0 = f(text_el.get('x')), f(text_el.get('y'))
    lines, cur_x, cur_y, buf = [], x0, y0, []
    if not len(text_el):
        s = ''.join(text_el.itertext()).strip()
        if s:
            lines.append((s, x0, y0, size, anchor, text_el))
        return lines
    for node in text_el.iter():
        tag = node.tag.split('}')[-1]
        if node is text_el:
            lead = (node.text or '')
            if lead.strip():
                buf.append(lead)
            continue
        if tag == 'tspan':
            if node.get('x') is not None:  # 新行开始
                s = ''.join(buf).strip()
                if s:
                    lines.append((s, cur_x, cur_y, size, anchor, text_el))
                buf = [node.text or '']
                cur_x = f(node.get('x'), x0)
                if node.get('dy') is not None:
                    cur_y = cur_y + f(node.get('dy'), 0.0)
            else:
                buf.append(node.text or '')
            tail = node.tail or ''
            if tail.strip():
                buf.append(tail)
    s = ''.join(buf).strip()
    if s:
        lines.append((s, cur_x, cur_y, size, anchor, text_el))
    return lines


def lint_svg(path: Path, tol: float, canvas=(1280.0, 720.0)):
    issues = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return [('error', path.name, f'XML 解析失败: {e}')]
    vb = root.get('viewBox')
    if vb:
        parts = vb.replace(',', ' ').split()
        canvas = (f(parts[2], canvas[0]), f(parts[3], canvas[1]))

    rects, segments, polys = collect_graphics(root)
    boxes = []  # (x1,y1,x2,y2,label,file)

    for text_el in root.iter():
        if text_el.tag.split('}')[-1] != 'text':
            continue
        for (s, x, y, size, anchor, el) in text_lines(text_el):
            w = est_width(s, size)
            if anchor == 'middle':
                x1 = x - w / 2
            elif anchor == 'end':
                x1 = x - w
            else:
                x1 = x
            y1, y2 = y - size * 0.8, y + size * 0.25
            x2 = x1 + w
            label = s[:18] + ('…' if len(s) > 18 else '')
            boxes.append((x1, y1, x2, y2, label))

            # 1) 画布越界
            if x1 < -tol or y1 < -tol or x2 > canvas[0] + tol or y2 > canvas[1] + tol:
                issues.append(('error', path.name,
                               f'越出画布: 「{label}」 est_box=({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}) canvas={canvas[0]:.0f}x{canvas[1]:.0f}'))
                continue
            # 2) 溢出所在容器:取锚点命中的最小实底 rect
            hit = [r for r in rects
                   if r['w'] >= 60 and r['h'] >= 30
                   and r['fill'] != 'none'
                   and r['x'] - tol <= x <= r['x'] + r['w'] + tol
                   and r['y'] - tol <= y <= r['y'] + r['h'] + tol]
            if hit:
                r = min(hit, key=lambda r: r['w'] * r['h'])
                pad = 4.0
                if (x1 < r['x'] - tol or x2 > r['x'] + r['w'] + tol
                        or y1 < r['y'] - tol or y2 > r['y'] + r['h'] + tol):
                    over_r = x2 - (r['x'] + r['w'])
                    over_b = y2 - (r['y'] + r['h'])
                    where = (f'右溢出 {over_r:.0f}px' if over_r > tol else
                             f'下溢出 {over_b:.0f}px' if over_b > tol else
                             f'左/上越界 (box=({x1:.0f},{y1:.0f}))')
                    issues.append(('error', path.name,
                                   f'溢出卡片: 「{label}」 {where} 卡片=({r["x"]:.0f},{r["y"]:.0f},{r["x"]+r["w"]:.0f},{r["y"]+r["h"]:.0f}) est_w={w:.0f}'))

    # 3) 文字互相重叠(不同 text 元素的行框交叠超小框 30%)
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ix = min(a[2], b[2]) - max(a[0], b[0])
            iy = min(a[3], b[3]) - max(a[1], b[1])
            if ix > 0 and iy > 0:
                inter = ix * iy
                smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if smaller > 0 and inter / smaller > 0.30:
                    issues.append(('warning', path.name,
                                   f'文字重叠: 「{a[4]}」 × 「{b[4]}」 交叠 {inter/smaller*100:.0f}%'))

    # 4) 悬空连线端点:折线只查首尾顶点(中间拐点是肘点);端点落在节点边缘或箭头/装饰 polygon 包围盒内即算连接
    def on_rect_edge(px, py):
        for r in rects:
            on_left = abs(px - r['x']) <= tol and r['y'] - tol <= py <= r['y'] + r['h'] + tol
            on_right = abs(px - (r['x'] + r['w'])) <= tol and r['y'] - tol <= py <= r['y'] + r['h'] + tol
            on_top = abs(py - r['y']) <= tol and r['x'] - tol <= px <= r['x'] + r['w'] + tol
            on_bottom = abs(py - (r['y'] + r['h'])) <= tol and r['x'] - tol <= px <= r['x'] + r['w'] + tol
            if on_left or on_right or on_top or on_bottom:
                return True
        return False

    def in_polygon(px, py):
        for (x1, y1, x2, y2) in polys:
            if x1 - tol <= px <= x2 + tol and y1 - tol <= py <= y2 + tol:
                return True
        return False

    connected = lambda p: on_rect_edge(*p) or in_polygon(*p)
    for seg in segments:
        if isinstance(seg[0], str):
            _, coords = seg
            ends = [coords[0], coords[-1]]  # 只查首尾
        else:
            ends = [seg[0], seg[1]]
        flags = [connected(p) for p in ends]
        if any(flags) and not all(flags):
            dangling = [p for p, ok in zip(ends, flags) if not ok]
            for (dx, dy) in dangling:
                issues.append(('warning', path.name,
                               f'连线端点悬空: ({dx:.0f},{dy:.0f}) 未落在任何节点边缘或箭头上'))

    # 5) 箭头三角必须指向某个节点:小 polygon(疑似箭头)的所有顶点都远离节点边缘(>12px)即告警
    def near_rect_edge(px, py, margin):
        for r in rects:
            if (abs(px - r['x']) <= margin and r['y'] - margin <= py <= r['y'] + r['h'] + margin) or \
               (abs(px - (r['x'] + r['w'])) <= margin and r['y'] - margin <= py <= r['y'] + r['h'] + margin) or \
               (abs(py - r['y']) <= margin and r['x'] - margin <= px <= r['x'] + r['w'] + margin) or \
               (abs(py - (r['y'] + r['h'])) <= margin and r['x'] - margin <= px <= r['x'] + r['w'] + margin):
                return True
        return False

    for (x1, y1, x2, y2) in polys:
        if (x2 - x1) > 40 or (y2 - y1) > 40:
            continue  # 大 polygon 是形状不是箭头
        corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
        if not any(near_rect_edge(px, py, 12.0) or on_rect_edge(px, py) for (px, py) in corners):
            issues.append(('warning', path.name,
                           f'箭头未指向节点: polygon ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) 附近无任何节点边缘'))
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='SVG 文件或目录')
    ap.add_argument('--tolerance', type=float, default=4.0, help='容差 px(默认 4)')
    args = ap.parse_args()

    p = Path(args.target)
    files = sorted(p.glob('*.svg')) if p.is_dir() else [p]
    if not files:
        print(f'未找到 SVG: {p}')
        return 2

    total_err, total_warn = 0, 0
    for fp in files:
        issues = lint_svg(fp, args.tolerance)
        errs = [i for i in issues if i[0] == 'error']
        warns = [i for i in issues if i[0] == 'warning']
        total_err += len(errs)
        total_warn += len(warns)
        status = 'OK' if not issues else f'{len(errs)} error, {len(warns)} warning'
        print(f'{fp.name}: {status}')
        for lvl, _, msg in issues:
            print(f'  [{lvl}] {msg}')

    print(f'\n合计: {total_err} error, {total_warn} warning, {len(files)} 文件')
    return 1 if total_err else (2 if total_warn else 0)


if __name__ == '__main__':
    sys.exit(main())
