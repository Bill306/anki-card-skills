# cards.json 格式 v1

脚本读取 UTF-8 JSON；内容字段是**纯文本**，会转义成 HTML，不能填任意 HTML。Anki 数学可用 `\( ... \)` / `\[ ... \]`，注意 JSON 反斜杠转义。媒体路径相对 cards.json 所在目录，只支持本目录及子目录内的 PNG/JPEG/WebP/GIF。

```json
{
  "schema_version": 1,
  "deck": {"id": "course.lumabox.intro", "name": "LumaBox::基础"},
  "sources": [
    {"id": "source-1", "title": "LumaBox 课堂笔记", "sha256": "64位十六进制PDF哈希", "page_count": 4}
  ],
  "concepts": [
    {"id": "checksum-length", "title": "校验码长度", "disposition": "included",
     "source_refs": [{"source_id": "source-1", "pages": [3]}]},
    {"id": "throughput", "title": "最大吞吐量", "disposition": "blocked",
     "reason": "资料未给数值，不生成卡；需要补充来源。",
     "source_refs": [{"source_id": "source-1", "pages": [4]}]}
  ],
  "cards": [
    {"id": "checksum-length", "type": "cloze",
     "question": "LumaBox 校验码长度为 {{c1::16}} 位。", "answer": "",
     "explanation": "", "concept_ids": ["checksum-length"],
     "source_refs": [{"source_id": "source-1", "pages": [3], "evidence": "校验码长度为16位。"}],
     "tags": ["存储", "校验"], "front_media": [], "back_media": []}
  ]
}
```

示例的 sha256 需替换为 prepare_pdf.py 输出的真实值。`page_count` 是整份 PDF 的物理页数；pages 使用从 1 开始的物理 PDF 页码，不是印刷页号。可选 `page_labels` 为与 pages 等长的印刷页标签数组，仅补充显示，不替代物理页码。

- source.id / deck.id / card.id / concept.id：1–100 位字母数字及 `._:-`，不要使用绝对路径。source.id 可用预处理给出的 hash id；deck/card.id 应在重复导出时保持稳定。
- 每个 concept 要有 title、disposition 与 source_refs。disposition 为 included / excluded / blocked；后两者必须有 reason。
- 每张卡引用至少一个 included 概念；所有 included 概念至少有一张卡。source_refs 必须包含 source_id、有效 pages 和 evidence。evidence 写原文短引或明确的图表定位与观察依据，供语义审查；脚本不判断其真伪。
- type 为 basic / cloze。Basic 必须有非空 answer；Cloze 的答案在 question 的 `{{c1::...}}` 内，answer 必须为空，解释放 explanation。
- 可选 tags 为无空白标签数组，`::` 可用于层级。可选 front_media / back_media 为图片相对路径数组；相同图片按内容哈希去重。
- 一个 Cloze note 本版只含一个 c1 空，因此导出的 notes 与 cards 数相同。选择题需要时用 basic，选项在 question，正确选项及依据在 answer/explanation。

## 产物

`deck.apkg` 是正式导入文件；`review.md` 和 `review.html` 是可读审阅稿；`cards.tsv` 含 NoteType/Id/Front/Back/Extra/Sources/Tags，作为人工检查或字段映射后的备用导入，不能直接冒充混合卡型的无配置导入文件。继续编辑原始 cards.json 后，导出到新目录。

`audit.json` 记录源页引用、缺口、notes/cards/media 数、GUID、依赖版本和包校验。status 仅代表结构检查及是否有 blocked 概念；页面内容和答案是否相符仍由 Agent 阅读验证。不要把 source 引用存在等同于事实正确。
