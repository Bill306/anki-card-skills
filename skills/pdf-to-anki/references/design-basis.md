# 设计依据与边界

本 Skill 是对公开产品行为和实际制卡经验的归纳，不依赖 Memo 账号或 API，不复制其前端应用代码，也不声称取得了隐藏系统提示词。

2026-10-20 的一次虚构笔记实测中，Memo 的可见执行记录显示读取 Master Skill、检索 notebook、读取 source page、保存 5 张卡。该观察的研究记录保留在发布者本地，不随仓库分发，因此它是设计背景，不是读者可在本仓库独立复查的后台实现证据。可见的制卡风格说明强调单一知识点、主动回忆与来源；其中一张实际卡仍同时问数字和作用。因此本 Skill 在“Skill + 来源 + 生成 + 导出”结构上增加显式知识点清单、双问题复核和覆盖说明。本仓库自有实现与示例的验证见根目录 docs/verification.md。

Memo 官方示例的 .apkg 含 notes/cards、来源字段和媒体；本实现使用独立开源库 genanki 生成标准包，未复制 Memo 导出实现。稳定 GUID 以卡片 ID 而非全文为依据，用于后续修订。

参考入口：

- [Memo Skills](https://www.memo.cards/skills)：产品展示的制卡风格。
- [Anki 官方导入说明](https://docs.ankiweb.net/manual/importing/packaged-decks)：.apkg 与更新行为。
- [Anki 官方制卡说明](https://docs.ankiweb.net/manual/editing)：notes/cards、简洁学习目标和字段。
- [genanki 官方仓库](https://github.com/kerrickstaley/genanki)：导出库、HTML 字段、媒体和 GUID。

没有从单次测试推导固定分块长度、模型选择、OCR 算法或提示词优先级。本版的单空 Cloze、概念清单和输出格式是本 Skill 的设计选择，不是声称 Memo 后台遵守同样协议。
