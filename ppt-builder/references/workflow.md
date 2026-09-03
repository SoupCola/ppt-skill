# ppt-builder Workflow

把主题、调研背景、论文/报告材料或要点,做成个人风格演示稿:澄清 → 大纲 → 逐页详化 → SVG 页面 → ppt-engine 导出 `.pptx`。

## Stage 0 — 澄清(头脑风暴)

一次只问一个维度,不堆问卷。按顺序澄清(用户已给的可跳过):

1. 主题 / 工作标题
2. 受众与场景(答辩 / 课程汇报 / 项目评审 / 商业路演 / 技术评审)
3. 页数或页数范围
4. 源内容(论文 / 报告 / Markdown / PDF / DOCX 摘录 / 要点 / 对话材料)
5. 背景调研(事实依据 / 市场现状 / 技术事实,供大纲 Context-aware)
6. 风格(汇报风格 `briefing-report` / 技术风格 `technical-deepdive` / 信息可视化图文风格 `infoviz` / 自定义 `styles/<name>.md`)
7. 视觉约束(配色 / 品牌 / 字体 / 模板路径,可选)
8. 输出形态(只要大纲 / SVG 页 / PPTX / 备注 / Q&A 页 / snapshot 兜底)

用户想快进时,带显式假设推进并列出来。风格选定后加载对应 `references/styles/*.md` 作为本份基调。

收齐后才进 Stage 1。

## Stage 1 — 生成大纲

用 `references/outline-prompt.md`(v2.0 Context-Aware 金字塔大纲),填入占位符:

- `{{TOPIC}}`、`{{CONTEXT}}`、`{{PAGE_REQUIREMENT}}`、`{{SOURCE_CONTENT}}`、`{{SCENARIO}}`、`{{AUDIENCE}}`

输出必须严格包裹:

```text
[PPT_OUTLINE]
{...valid JSON...}
[/PPT_OUTLINE]
```

新大纲 schema(`cover` / `table_of_contents` / `parts[]` / `end_page`),每页 `content` **填 3–5 条要点**,不要留空数组。

质量检查:

- 页数符合要求。
- 整份有一个核心主张;每页有一句可被论证的核心结论,不是主题词。
- 页序有清晰逻辑链。
- evidence/context 字段不虚构;材料不足写进 `missing_information`。
- 输出是可解析 JSON:双引号、无注释、无尾随逗号。

## Stage 2 — 逐页内容详化

把大纲每页扩成一份简洁实现计划,供 Stage 3 的 SVG 提示词使用:

- 页码与标题
- 核心结论(一句可论证判断)
- 内容层级 + 1–5 条支撑要点
- 证据或源材料片段(可追溯)
- 视觉策略(见选定风格文件的布局偏好)
- Bento Grid 卡片数量与相对尺寸
- 建议的顶层 SVG 语义分组 `<g id="...">`
- 可选演讲备注提示

推荐页型:

- 封面:标题、副标题、作者/场景,克制视觉钩子。
- 目录/结构:高层路线图。
- 章节分隔:一句短陈述 + 视觉过渡。
- 内容页:Bento Grid,1 主卡 + 支撑卡。
- 数据页:大指标卡、图表、注释 callout。
- 对比页:两栏 / 2×2 卡,清晰标签。
- 流程页:横向时间线或步骤卡。
- 结论页:精炼 takeaway + 下一步。
- Q&A / 附录页:预期问题或答辩备用页。

## Stage 3 — 生成 SVG 页面

用 `references/svg-page-prompt.md`(含共享 Bento 布局规则、**文字宽度预算与对齐硬规则**)+ 选定风格文件,逐页生成。

硬约束:

- 一页一个完整 SVG。
- `width="1280" height="720" viewBox="0 0 1280 720"`。
- 含页面背景 `<rect>`。
- 内容页优先 Bento Grid,卡片间 ≥ 20px 间距,四周安全边距。
- 遵守 `svg-page-prompt.md` 的 Native-PPTX-friendly SVG 约束,避免 ppt-engine native 导出不支持的特性。
- 遵守**文字宽度预算**(中文 ≈ 1.0×字号、英文/数字 ≈ 0.55×字号,行宽 ≤ 卡片内宽 − 2×16px)、居中标签必须 `text-anchor="middle"`、连线端点取节点边框几何中点。

**每页生成后立即过 lint 质量门**(ppt-builder 自带,零依赖):

```bash
python "<ppt-builder路径>/scripts/svg_text_lint.py" <svg_output目录>
```

- 基于同一套宽度预算公式做几何检查:文字溢出卡片、越出画布、文字互相重叠、连线端点悬空。
- `error`(溢出/越界)必须修复后重跑至清零;`warning`(文字重叠/悬空端点)逐条判断,属实则修。
- 修复优先改几何(卡片加宽/文字换行/端点对齐到边框中点),不要整体缩字号。

高风险页(嵌真实图、复杂链路图、密集矩阵)在 lint 之外再做**渲染回检**:

```bash
python "<ppt-engine路径>/scripts/visual_review.py" <project_path> --pages 03 05
```

Playwright + CJK 字体回退渲染 PNG 到 `<project>/.preview/`,肉眼或视觉模型复核版式;发现位置问题回到本 Stage 修 SVG,再重跑 lint,通过后才进 Stage 4。

复杂链路/流程图(≥6 节点或含分叉)建议**预布局**:用 dagre(5.8k★)/elkjs(2.75k★) 以 JSON 描述节点与边、由布局引擎输出坐标与连线拐点,再把坐标转写为原生安全 SVG——布局智能化、输出仍可编辑。禁止直接粘贴 mermaid/d2 输出的 SVG(含 CSS/marker,违反 Native-PPTX 约束)。

建议文件放置(ppt-engine 项目内):

```text
<project_path>/svg_output/page_001.svg
<project_path>/svg_output/page_002.svg
...
<project_path>/notes/total.md
```

不批量脚本生成 SVG,逐页设计。

## Stage 4 — 导出(ppt-engine)

后端路径与命令见 `references/ppt-engine.md`。`ppt-engine` 与 `ppt-builder` 在本仓库中同级,按相对路径定位(可移植变量定义见 `references/ppt-engine.md`)。流程:

```bash
# PPT_ENGINE 定位见 references/ppt-engine.md(ppt-builder 的同级 ../ppt-engine 目录)
PPT_ENGINE="$SKILL_DIR/../ppt-engine"

# 1. 初始化项目(如需)
python "$PPT_ENGINE/scripts/project_manager.py" init <project_name> --format ppt169

# 2. 导入源文件(如需)
python "$PPT_ENGINE/scripts/project_manager.py" import-sources <project_path> <source_files...> --move

# 3. 拆分备注(如有 notes/total.md)
python "$PPT_ENGINE/scripts/total_md_split.py" <project_path>

# 4. SVG 定稿
python "$PPT_ENGINE/scripts/finalize_svg.py" <project_path>

# 5. 导出 PPTX
python "$PPT_ENGINE/scripts/svg_to_pptx.py" <project_path>
```

Windows 上若 `python3` 不可用,用 `python`,脚本路径相同。

输出模式:

- **Native/default**(首选):受支持的 SVG 原语/文本转原生 DrawingML,可编辑性最好。
- `--merge-paragraphs`:长正文编辑优先,可能改变换行。
- `--svg-snapshot`:额外出一份视觉参考快照 PPTX,可编辑性差。
- `--only native` / `--only legacy`:严格 native 检查 / 兜底参考。

按需选用,不要默认全开。

## 完成校验

- Stage 3 lint 清零(error=0,warning 已逐条裁决)。
- 确认 `.pptx` 存在于项目导出/输出位置。
- 确认无 native 导出报错;若用了 snapshot 兜底,记录原因。
- 导出后用 PowerPoint COM 或 ppt-engine `visual_review.py` 渲染 PNG 快速复核;可能的话请用户在 PowerPoint/WPS 打开确认视觉与可编辑性。

## 完成报告模板

```markdown
## PPT Build Complete

### Inputs Used
- Topic: <topic>
- Scenario/Audience: <scenario and audience>
- Page count: <count>
- Style: <briefing-report | technical-deepdive | custom>

### Files Created
- Outline: `<path or conversation output>`
- SVG pages: `<project svg path>`
- PPTX: `<pptx path>`

### Output Mode
- Mode: Native editable / Snapshot / Mixed fallback
- Editability note: <what stays editable, known limits>

### Summary
1. Stage 0 澄清需求
2. Stage 1 金字塔大纲(v2.0 Context-Aware)
3. Stage 2 逐页内容详化
4. Stage 3 Bento Grid SVG 页面
5. Stage 4 ppt-engine 定稿并导出 PPTX

### Caveats / Next Steps
- <missing info, unsupported effects, manual review, refinements>
```
