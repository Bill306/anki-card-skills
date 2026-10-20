# lumabox-test

Source ID: pdf-7d6f528a6fc99120

SHA256: 7d6f528a6fc99120b6ec4813a7f57a105db2b0ed1639d62755f69ee37ccfdcb8


## PDF p.1 (label: )

Flags: none; visual review still needed

LumaBox：缓存与归档

自编测试资料；不代表真实产品。



缓存层用于快速临时存取；断电后缓存数据丢失。


归档层用于长期保存；断电后归档数据仍保留。


对比表：


存储层 用途   断电后的数据


缓存层 快速临时存取 丢失


归档层 长期保存  保留





课堂讲义 / 物理 PDF 第 1 页


## PDF p.2 (label: )

Flags: none; visual review still needed

LumaBox：写入流程

自编测试资料；不代表真实产品。



写入顺序：进入缓存 → 完成校验 → 写入归档。


只有完成写入归档，数据才被标记为已持久保存。


仅进入缓存或完成校验都不算持久保存。


流程图：缓存 → 校验 → 归档 → 已持久保存





课堂讲义 / 物理 PDF 第 2 页


## PDF p.3 (label: )

Flags: none; visual review still needed

LumaBox：校验与冗余

自编测试资料；不代表真实产品。



校验码长度为 16 位。


校验用于检测数据损坏；不能单靠校验码恢复数据。


系统保存两份独立副本。


其中一份损坏且另一份完整时，可从完整副本恢复。


两份副本都损坏时，不能依靠这两份副本恢复。





课堂讲义 / 物理 PDF 第 3 页


## PDF p.4 (label: )

Flags: sparse_text_check_scan_or_diagram, contains_images_or_vectors_check_visuals
