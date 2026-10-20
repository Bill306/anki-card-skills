# PDF→Anki 测试::LumaBox

核对卡片来源、单一考点、答案与覆盖；自动校验不代替语义复核。


## cache-purpose · basic

在 LumaBox 中，缓存层用于哪类数据存取？

答案：快速、临时的数据存取。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.1

证据：缓存层用于快速临时存取；断电后缓存数据丢失。


## archive-purpose · basic

在 LumaBox 中，归档层用于哪类数据保存？

答案：长期保存。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.1

证据：归档层用于长期保存；断电后归档数据仍保留。


## cache-power · cloze

LumaBox 断电后，缓存层的数据会{{c1::丢失}}。

答案：见填空目标

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.1

证据：断电后缓存数据丢失。


## archive-power · basic

LumaBox 断电后，归档层的数据会怎样？

答案：仍保留。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.1

证据：断电后归档数据仍保留。


## write-order · basic

LumaBox 写入数据的三个步骤依次是什么？

答案：进入缓存 → 完成校验 → 写入归档。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.2

证据：写入顺序：进入缓存 → 完成校验 → 写入归档。


## persist-condition · basic

LumaBox 在完成哪一步后，才将数据标记为已持久保存？

答案：完成写入归档后。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.2

证据：只有完成写入归档，数据才被标记为已持久保存。


## checksum-length · cloze

LumaBox 的校验码长度为 {{c1::16}} 位。

答案：见填空目标

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.3

证据：校验码长度为 16 位。


## checksum-boundary · basic

LumaBox 校验码能对数据损坏提供什么能力？

答案：检测损坏；不能单靠校验码恢复已损坏的数据。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.3

证据：校验用于检测数据损坏；不能单靠校验码恢复数据。


## recovery-condition · basic

LumaBox 的一份副本损坏时，要从另一副本恢复，另一副本必须满足什么条件？

答案：另一份副本必须完整。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.3

证据：其中一份损坏且另一份完整时，可从完整副本恢复。


## both-corrupt · basic

LumaBox 两份副本都损坏时，依靠这两份副本能得到什么恢复结果？

答案：不能依靠这两份副本恢复数据。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.3

证据：两份副本都损坏时，不能依靠这两份副本恢复。


## measured-rate · basic

LumaBox 示例测量中，80 MiB 数据在 4 秒内完成写入，平均写入速率是多少？

答案：20 MiB/秒。

补充：80 ÷ 4 = 20；单位为 MiB/秒。仅描述这次测量。

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.4

证据：本次平均写入速率 = 80 MiB / 4 秒 = 20 MiB/秒。


## measurement-limit · basic

从 LumaBox 示例的 20 MiB/秒测量值，能对系统最大吞吐量作何判断？

答案：不能将该测量值视为最大吞吐量；资料未提供最大吞吐量数值。

补充：

来源：LumaBox 虚构课堂笔记（含扫描页） — PDF p.4

证据：这个测量值不能视为系统的最大吞吐量。最大吞吐量：本资料没有提供该数值。


# 知识点覆盖

- cache-purpose · 缓存用途 · included

- archive-purpose · 归档用途 · included

- cache-power · 缓存断电行为 · included

- archive-power · 归档断电行为 · included

- write-order · 写入顺序 · included

- persist-condition · 持久化条件 · included

- checksum-length · 校验码长度 · included

- checksum-boundary · 校验的能力边界 · included

- recovery-condition · 恢复所需副本条件 · included

- both-corrupt · 冗余恢复的失败边界 · included

- measured-rate · 测量平均速率 · included

- measurement-limit · 测量结果的推断边界 · included

- repeated-cache · 第4页重复的缓存断电提醒 · excluded：与 cache-power 重复，合并至同一考点。

- maximum-rate · 最大吞吐量具体数值 · blocked：原文明确未提供；保留缺口，不捏造数值。需补充真实规格来源。