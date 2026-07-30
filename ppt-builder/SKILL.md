---
name: ppt-builder
description: |
  从主题、调研背景、论文/报告材料或要点出发,先做澄清式头脑风暴确认需求,再用金字塔原理产出大纲、逐页内容详化、1280×720 SVG Bento 页面设计,最终通过本地 ppt-engine 导出可编辑 .pptx。用于答辩、汇报、路演、技术评审等叙事型演示稿。
  触发:用户说"帮我做答辩/汇报 PPT"、"把这篇论文/报告做成演示稿"、"生成 PPT 大纲/幻灯片结构/演讲备注/封面目录/Q&A 页"、"设计 SVG 幻灯片(Bento Grid)"、"产出可编辑 pptx"。
  不用于独立架构图/模块图/网络图/流程图等结构图(走 figure-builder);不用于论文写作/文献综述(走 bishe-guider);不用于 Markdown/DOCX 转换(走 markdown2docx)。导出阶段调用 ppt-engine,不要单独触发后者做演示稿。
---

# PPT Builder

把主题、调研背景、论文/报告材料或要点,做成个人风格的叙事演示稿:**澄清 → 大纲 → 逐页详化 → 1280×720 SVG Bento 页面 → ppt-engine 导出可编辑 .pptx**。

## 何时用

用户说:

- 帮我做答辩/汇报/路演/技术评审的 PPT;
- 把这篇论文/报告/材料做成演示稿;
- 生成 PPT 大纲、幻灯片结构、演讲备注、封面/目录/Q&A 页;
- 设计 1280×720 SVG 幻灯片(Bento Grid 布局);
- 产出可编辑 `.pptx` 叙事稿。

## 何时不用

- 独立架构图 / 模块图 / 网络图 / 流程图 / 结构图 → `figure-builder`
- 论文写作 / 文献综述 → `bishe-guider`
- Markdown / DOCX 转换 → `markdown2docx`
- 直接导出或排障 ppt-engine 脚本 → `ppt-engine`(本技能在导出阶段会调用它,用户不需单独触发)

## 风格路由

开工前先和用户对齐风格。本技能内置两种预设,各是一个 `references/styles/*.md` 文件:

- **汇报风格**(管理评审型)→ `references/styles/briefing-report.md`:领导/评委,结论先行,商务留白,克制 Bento。
- **技术风格**(工程评审型)→ `references/styles/technical-deepdive.md`:架构师/同行,架构图 + 方案对比,密集混合网格。

新增风格:在 `references/styles/` 加一个 md 文件即可,无需改 SKILL.md。SKILL.md 只靠文件名约定风格路由,Stage 0 选定后加载对应文件作为本份的视觉与密度基调。

## 工作流(5 阶段)

完整流程见 `references/workflow.md`。概要:

1. **Stage 0 澄清(头脑风暴)** — 见下节。一次只问一个维度,收齐才进下一阶段。
2. **Stage 1 大纲** — 用 `references/outline-prompt.md`(v2.0 Context-Aware 金字塔大纲),产出 `[PPT_OUTLINE]...[/PPT_OUTLINE]` JSON,每页 `content` 填 3–5 条要点。
3. **Stage 2 逐页详化** — 把大纲每页扩成:核心结论 + 支撑要点/数据 + 证据溯源 + 视觉策略 + Bento 卡片结构 + 备注提示,喂给 Stage 3。
4. **Stage 3 SVG 生成** — 用 `references/svg-page-prompt.md`(含共享 Bento 布局规则)+ 选定风格文件,逐页生成 1280×720 SVG。
5. **Stage 4 导出** — 调用 ppt-engine 定稿并导出 PPTX,见 `references/ppt-engine.md`。报告最终路径与可编辑性。

## Stage 0 澄清怎么做

cs-brainstorm 风格:AI 是思考伙伴,不是记录员。一次只问一个维度,不堆问卷。按顺序澄清(用户已给的可跳过):

1. **主题 / 工作标题** — 这份 PPT 讲什么。
2. **受众与场景** — 答辩 / 课程汇报 / 项目评审 / 商业路演 / 技术评审;受众是导师、评委、同学、客户、同行。
3. **页数** — 固定页数或范围。
4. **源内容** — 论文 / 报告 / Markdown / PDF / DOCX 摘录 / 要点 / 对话材料。
5. **背景调研** — 如有,提供事实依据 / 市场现状 / 技术事实,供大纲 Context-aware。
6. **风格** — 汇报风格 / 技术风格 / 自定义(指向某个 `references/styles/*.md`)。
7. **视觉约束** — 配色 / 品牌 / 字体 / 模板路径(可选)。
8. **输出形态** — 只要大纲 / SVG 页 / PPTX / 备注 / Q&A 页 / snapshot 兜底。

用户想快进时,带显式假设推进并列出来,不要卡在等回答。风格选定后,加载对应 `references/styles/*.md` 作为本份的视觉与密度基调。

## 每页充实但不堆文字墙

硬性内容标准:

- 每页必须有**一句可被论证的核心结论**,不能只有主题词。
- 每页含**核心结论 + 支撑要点/数据 + 证据溯源**三要素。
- 正文 ≥ 约 120 字(技术风格可到 ~200 字),但必须**拆成 Bento 卡片**,不得形成大段文字墙。
- 不得虚构事实、数据、案例、引用;材料不足时在 outline 的 `missing_information` 说明。

## 硬边界

1. **不跳过 Stage 0** — 没收齐主题/受众/页数/源内容就开工,大纲会跑偏。
2. **不虚构** — 大纲与 SVG 只能用输入提供的事实/数据。
3. **不替 ppt-engine 做导出** — Stage 4 只调用 ppt-engine 脚本,不重写导出逻辑。
4. **不批量脚本生成 SVG** — 逐页设计质量靠每页决策,除非用户明确改流程。
5. **风格扩展只加文件** — 新增风格只在 `references/styles/` 加 md,不动 SKILL.md 主体。

## 参考

- `references/workflow.md` — 完整 input→output 流程与完成报告模板。
- `references/outline-prompt.md` — v2.0 Context-Aware 金字塔大纲提示词。
- `references/svg-page-prompt.md` — 1280×720 SVG 页面提示词 + 共享 Bento Grid 布局规则。
- `references/ppt-engine.md` — 全局 ppt-engine 后端路径、命令、依赖、输出模式、风险。
- `references/styles/briefing-report.md` — 汇报风格(管理评审型)预设。
- `references/styles/technical-deepdive.md` — 技术风格(工程评审型)预设。
