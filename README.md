# ppt-skill

自包含、可移植的 Claude skill 组合，用于制作演示稿：从主题 / 调研背景 / 论文 / 报告 → 大纲 → 逐页 SVG（1280×720 Bento Grid）→ 经本地 SVG 转 PPTX 引擎导出可编辑 `.pptx`。

仓库根下两个 skill 同级放置：

| Skill | 角色 |
| --- | --- |
| **ppt-builder** | 入口 skill。主题澄清 → 大纲 JSON → 逐页内容详化 → 个人风格 SVG 页面提示词。导出阶段调用 `ppt-engine`。 |
| **ppt-engine** | 内部后端。项目管理、SVG 定稿/检查、SVG 转 PPTX 导出工具。（vendor 自上游 `hugohe3/ppt-master`，MIT） |

两个 skill **同级共存**，`ppt-builder` 通过相对同级路径访问 `ppt-engine`——因此仓库在任意位置 clone 均可运行。

## 快速开始（新机器）

```bash
git clone https://github.com/SoupCola/ppt-skill.git
cd ppt-skill

# 安装后端 Python 依赖
pip install -r ppt-engine/requirements.txt
```

然后在 Claude 会话中触发 `ppt-builder` skill（如「帮我做个答辩 PPT」）。也可直接调用脚本：

```bash
PE=ppt-engine
python "$PE/scripts/project_manager.py" init my_deck --format ppt169
python "$PE/scripts/finalize_svg.py" projects/my_deck
python "$PE/scripts/svg_to_pptx.py" projects/my_deck
```

## 目录结构

```
ppt-skill/
├── ppt-builder/                # 入口 skill（提示词、工作流、风格）
│   ├── SKILL.md
│   └── references/
├── ppt-engine/                 # 后端 skill（脚本、模板、工作流）
│   ├── SKILL.md
│   ├── scripts/                # project_manager、finalize_svg、svg_to_pptx 等
│   ├── templates/              # brands / charts / decks / icons / layouts
│   ├── workflows/
│   └── requirements.txt
├── README.md
└── LICENSE
```

## 可移植性

- `ppt-builder/references/ppt-engine.md` 与 `workflow.md` 通过
  `$SKILL_DIR/../ppt-engine`（同级目录）引用 `ppt-engine`，**而非**绝对路径。
  任意系统、任意 clone 位置均可用。
- `ppt-engine` 脚本用 `__file__` 定位自身路径，无硬编码绝对路径。
- 可选能力（PDF/文档/网页转换、AI 配图、旁白、实时 SVG 编辑器）需额外依赖，
  见 `ppt-engine/requirements.txt`。最小 PPTX 导出仅需 `python-pptx`。

## 上游与 license

`ppt-engine` vendor 自 <https://github.com/hugohe3/ppt-master.git>
（MIT License，版权 2025-2026 Hugo He），仅做了目录重命名与 SKILL.md frontmatter
调整，未改动其代码逻辑。本仓库 `LICENSE` 保留了 MIT License 条款。
