# ppt-engine Backend Reference

`ppt-builder` 是个人风格的入口 skill，存储大纲/SVG 提示词与工作流，使用同级目录下的 `ppt-engine` 作为 PPTX 后端/工具源。两个 skill 在本仓库中同级放置，因此可相对定位，任意 clone 位置都能运行。

## 后端路径（可移植定位）

两个 skill 在仓库中同级，`ppt-engine` 位于 `ppt-builder` 的同级目录。定义变量时基于 ppt-builder 自身目录推导，避免硬编码绝对路径：

```bash
# ppt-builder/SKILL.md 所在目录即为 SKILL_DIR；ppt-engine 是其同级目录
SKILL_DIR="$(dirname "$(readlink -f "$0")")"   # 或按调用上下文取 ppt-builder 目录
PPT_ENGINE="$SKILL_DIR/../ppt-engine"
```

PowerShell：

```powershell
# 假设当前在 ppt-builder 目录内
$SKILL_DIR = (Get-Location).Path
$PPT_ENGINE = Join-Path $SKILL_DIR "..\ppt-engine"
```

> 关键：`ppt-engine` 始终是 `ppt-builder` 的同级目录，无论仓库 clone 到何处，该相对关系不变。**不要**把 `ppt-engine` 路径写死为绝对路径。

## Upstream 与 license

- 上游仓库：<https://github.com/hugohe3/ppt-master.git>
- License：MIT License，copyright 2025-2026 Hugo He.
- `ppt-engine` 由上游本地 vendor 而来，仅重命名目录与 frontmatter，未改动其代码逻辑。如未来复制或改写上游大量代码/skill 内容，保留 MIT license 注记与版权。

## Pipeline 形态

`ppt-engine` 是 SVG-first：

```text
source content → Markdown normalization → project init/import → SVG authoring → SVG finalization → PPTX export
```

`ppt-builder` 的分层：

```text
ppt-builder: topic/context → outline JSON → slide content plan → personal-style SVG prompt
ppt-engine : project structure → SVG finalization/checking → SVG-to-PPTX export
```

## 常用命令

```bash
PPT_ENGINE="$SKILL_DIR/../ppt-engine"

# 初始化项目
python "$PPT_ENGINE/scripts/project_manager.py" init <project_name> --format ppt169

# 导入源文件
python "$PPT_ENGINE/scripts/project_manager.py" import-sources <project_path> <source_files...> --move

# 拆分备注(notes/total.md → 各页)
python "$PPT_ENGINE/scripts/total_md_split.py" <project_path>

# SVG 定稿
python "$PPT_ENGINE/scripts/finalize_svg.py" <project_path>

# 导出 PPTX
python "$PPT_ENGINE/scripts/svg_to_pptx.py" <project_path>
```

Windows 上若 `python3` 不可用，用 `python`，脚本路径相同。

不要在 `ppt-builder` 工作流中 clone 或下载上游；使用本地同级已存在的 `ppt-engine` 目录。

## 输出模式

- **Native/default**（首选）：受支持的 SVG 原语/文本转原生 PowerPoint DrawingML，可编辑性最好。
- **`--merge-paragraphs`**：编辑优先的长正文模式，可能改变换行。
- **`--svg-snapshot`**：额外出一份 SVG/PNG 快照 PPTX 作视觉参考，可编辑性差。
- **`--only legacy`**：旧式基于图像的输出，仅作兜底/参考。
- **`--only native`**：仅 native DrawingML，用于严格可编辑输出检查。

报告最终输出时，明确说明是 native editable、snapshot，还是 mixed/fallback。不要承诺所有视觉效果都可编辑。

## 按能力的依赖

最小/native PPTX 导出：

- Python 运行时
- `python-pptx>=0.6.21`
- `ppt-engine/scripts/` 标准库工具

源文件转换：

- PDF：`PyMuPDF`
- DOCX/HTML/EPUB/IPYNB：`mammoth`、`markdownify`、`ebooklib`、`nbconvert`
- Excel：`openpyxl`
- Web：`requests`、`beautifulsoup4`，可选 `curl_cffi`
- 少见文档格式可能需要 `pandoc`

快照/兼容路径：

- 优先 CairoSVG，或 `svglib` + `reportlab`

可选特性：

- 图像处理：`Pillow`、`numpy`
- AI 图像生成：provider 包/API 凭证（如 `google-genai` 或 OpenAI 兼容 HTTP）
- 旁白：`edge-tts`、音频工具、`ffprobe` 探测时长
- SVG 编辑器/实时工具：`flask`

安装依赖：

```bash
pip install -r ppt-engine/requirements.txt
```

未获用户明确要求前，不安装或改变依赖。首次使用时检查依赖即可。

## Native-friendly SVG 指南

`ppt-engine/references/shared-standards.md` 是详细约束的权威来源。在 `ppt-builder` 提示词中优先：

- 16:9 PPT 用 1280×720 画布：`viewBox="0 0 1280 720"`。
- 基础形状、直接文本、显式内联 SVG 属性。
- 顶层语义 `<g id="...">` 分组。
- XML 安全文本与属性。
- 字体以常见已安装字体族结尾。

避免：

- `<style>`、CSS class、外部 CSS。
- `<foreignObject>`、`<symbol>/<use>`、`textPath`、`@font-face`。
- SVG 动画、脚本、事件处理器、iframe。
- `mask`、group opacity、image opacity、`rgba(...)`。
- 需要 native 可编辑性时的复杂滤镜/裁剪/像素级透明合成。

## 风险

- native SVG-to-PPTX 转换很严格，不支持的 SVG 特性会导出失败而非静默栅格化。
- snapshot/legacy 输出视觉可用，但不等于完全可编辑的 PowerPoint 形状。
- 文本可编辑性与 SVG 精确换行可能冲突；长段落编辑更重要时用 `--merge-paragraphs`。
- `ppt-engine` 路径通过同级目录相对定位，仓库整体移动不影响；单独移动 `ppt-engine` 需同步更新本引用。
- 上游会随时间变化。当前版本以仓库内 `ppt-engine` 为现行后端，不在线拉取。
