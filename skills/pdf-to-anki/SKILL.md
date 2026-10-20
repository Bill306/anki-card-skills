---
name: pdf-to-anki
description: 把 PDF 课件、教材和课堂笔记转为带页码来源的 Anki 问答或填空卡，复核知识点覆盖与卡片质量，并导出可导入 Anki 的 .apkg、审阅文档和可更新的卡片 JSON。适用于 PDF→Anki、笔记制卡、制作牌组；仅解释 Anki 用法时无需使用。
---

# PDF → Anki

交付能学习的卡组，而非每页一张的摘要。由当前 Agent 阅读资料、选点和审卡；脚本只做本地 PDF 预处理、数据校验与导出，不调用 Memo 或另一个模型服务。

## 工作流

1. **确定范围。** 查看用户提供的 PDF；仅追问影响结果且无法从材料推断的信息。未指定时：沿用材料语言；问答为主，适合精确记忆的术语/公式用单空填空；按有效知识点决定数量；牌组名用文件标题。用户指定数量时先检查可支持的独立知识点，数量不足要说明，不能凑卡。PPT 先取得 PDF 版本，不能声称已经处理备注页。
2. **读取与定位。** 用 `scripts/prepare_pdf.py input.pdf --out work/source-a` 输出逐页文字、页标签和 PNG。阅读全文，并查看渲染页中的图表、公式、脚注与顺序；多栏文本不能仅按抽取结果猜阅读顺序。扫描页用可用的视觉/OCR能力读 PNG，转录另存为带来源 ID 和物理页码的文本；认不清的数值或符号标为 blocked。先读目录/学习目标，再按章节阅读；长文分批，最终合并去重。只选择部分页时，在交付中明确范围。
3. **先列知识点再制卡。** 在 `cards.json` 为候选概念记录来源和 included/excluded/blocked。优先定义、条件、机制、对比、程序、公式和适用边界；目录、参考文献及重复说明一般排除并说明原因。将 included 概念映射到卡片；不是逐句转卡，也不能仅凭关键词搜索代替通读。
4. **生成草稿。** 读取 [制卡规则](references/card-rules.md)；按 [数据格式](references/schema.md) 写 `cards.json`。每个答案必须有来源证据和物理 PDF 页码。把原文事实与你的补充解释分开；默认不引入资料外事实。需要外部纠错时单列冲突与来源，不能悄悄改写教材。
5. **复核后修订。** 逐卡检查：来源是否真的支持答案、是否只考一个可独立判分的目标、条件/单位/否定/例外是否丢失、题干是否泄漏答案、是否与别卡重复。尤其拆开“长度是多少、作用是什么”这类双问题。对照概念清单补漏，记录未覆盖原因。看图确认图题/遮挡不会暴露答案；普通整页图宜放在背面。审阅文档不是要求用户先批准的流程；Agent 可完成常规复核后继续导出。
6. **导出并验包。** 执行 `scripts/export_anki.py cards.json --out output`，生成 `deck.apkg`、`cards.tsv`、`review.html`、`review.md`、`audit.json`。修复硬错误，逐项判断警告；脚本校验只证明结构、引用范围和包完整性，不证明语义正确。检查预览；若有 Anki 测试后端/隔离配置可用，验证实际导入，避免向用户真实牌组写入来测试。
7. **交付。** 链接 `.apkg`、可修改的 `cards.json`、审阅文档；报告来源页范围、notes/cards 数、待核对项及验证级别。导入方式：Anki → File/文件 → Import/导入 → 选择 `.apkg`。仅生成包不代表已导入用户 Anki；没有授权不自动导入或同步。

## 稳定更新与文件

- 初次给 deck.id 设稳定的课程/材料命名空间，card.id 代表同一个考点；修答案保留 ID，换考点或卡型用新 ID。脚本用 deck.id + card.id 生成 GUID，重复导出不会因答案措辞改变而生成新身份。导入更新仍受 Anki 的导入选项和本地修改影响。
- 多 PDF 的每份来源使用独立 id，sources 中保留 SHA256 和页数。PDF 换版本后更新来源信息并重新核对页码；不要直接沿用旧引用。
- 原文件、用户已修改的 JSON 和旧牌组必须保留；输出目录需不存在，重跑使用新目录。只交付明确产物，不打包用户原始 PDF、绝对路径或其他私有资料；用户需要可离线查看的证据图时，明确纳入对应本地图片。
- 图片通过 `front_media/back_media` 放入包；本版支持图片辅助的 Basic/Cloze，**不实现原生 Image Occlusion**。不要用未遮挡的标注图冒充图片遮挡卡。选择题可在需要时写成 Basic 卡，但不强制五选项。

## 运行环境

Python 3.10+；用可用 Python 建独立虚拟环境并安装本目录 `requirements.txt`，然后用该环境的 Python 执行脚本。不要把机器上的绝对 Python 路径写成 Skill 依赖。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r /path/to/pdf-to-anki/requirements.txt
.venv/bin/python /path/to/pdf-to-anki/scripts/prepare_pdf.py input.pdf --out work/source-a
# Agent 阅读 work/source-a 后，按 schema 编写 cards.json，并完成语义复核。
.venv/bin/python /path/to/pdf-to-anki/scripts/export_anki.py cards.json --out output
```

设计依据及与 Memo 实测的区别见 [来源说明](references/design-basis.md)，仅在需要解释设计时读取。
