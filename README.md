# ppt-skill

A self-contained, portable pair of Claude skills for building presentation decks: from a topic / research background / paper / report → outline → per-page SVG (1280×720 Bento Grid) → editable `.pptx` via a local SVG-to-PPTX engine.

Two skills live side-by-side at the repo root:

| Skill | Role |
| --- | --- |
| **ppt-builder** | Entry skill. Topic clarification → outline JSON → per-page content plan → personal-style SVG page prompt. Calls `ppt-engine` at export. |
| **ppt-engine** | Internal backend. Project management, SVG finalization/checking, SVG-to-PPTX export tooling. (vendored from upstream `hugohe3/ppt-master`, MIT) |

Both skills are **co-located** so `ppt-builder` reaches `ppt-engine` by a relative sibling path — the repo works at any clone location.

## Quick start (new machine)

```bash
git clone https://github.com/SoupCola/ppt-skill.git
cd ppt-skill

# Install Python dependencies for the engine
pip install -r ppt-engine/requirements.txt
```

Then in a Claude session, trigger the `ppt-builder` skill (e.g. "帮我做个答辩 PPT"). For direct script use:

```bash
PE=ppt-engine
python "$PE/scripts/project_manager.py" init my_deck --format ppt169
python "$PE/scripts/finalize_svg.py" projects/my_deck
python "$PE/scripts/svg_to_pptx.py" projects/my_deck
```

## Layout

```
ppt-skill/
├── ppt-builder/                # entry skill (prompts, workflow, styles)
│   ├── SKILL.md
│   └── references/
├── ppt-engine/                 # backend skill (scripts, templates, workflows)
│   ├── SKILL.md
│   ├── scripts/                # project_manager, finalize_svg, svg_to_pptx, ...
│   ├── templates/              # brands / charts / decks / icons / layouts
│   ├── workflows/
│   └── requirements.txt
├── README.md
└── LICENSE
```

## Portability

- `ppt-builder/references/ppt-engine.md` and `workflow.md` reference
  `ppt-engine` via `$SKILL_DIR/../ppt-engine` (sibling directory), **not** an
  absolute path. Works on any OS / any clone location.
- `ppt-engine` scripts resolve their own paths via `__file__` — no hardcoded
  absolute paths.
- Optional capabilities (PDF/doc/web conversion, AI image gen, narration,
  live SVG editor) require extra deps — see `ppt-engine/requirements.txt`.
  Minimal PPTX export needs only `python-pptx`.

## Upstream & license

`ppt-engine` is vendored from <https://github.com/hugohe3/ppt-master.git>
(MIT License, copyright 2025-2026 Hugo He), with only directory rename and
SKILL.md frontmatter changes — no code logic changes. MIT License terms are
preserved in this repo's `LICENSE`.
