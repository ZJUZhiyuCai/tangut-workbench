# 数据格式 v0.1

权威编辑数据位于 `data/`，全部为 UTF-8。网页 `dataset.json`、统计和 CLDF 均从这些文件生成，不手工维护第二套释义。JSONL 的字头索引由固定 Unicode 文件重建。

| 文件 | 主键与联系 | 说明 |
| --- | --- | --- |
| `characters.jsonl` | `U17788` | 一个 Unicode 标量；原始 `kTGT_MergedSrc` 与 `kTGT_RSUnicode` 值不改写 |
| `entries.json` | `lex-17788`；`character_ids` | 单字／多字词条，字序必须匹配所引字符 |
| `senses.json` | `lex-17788-01`；`entry_id` | 一个义项、证据状态、独立复核记录与来源定位 |
| `sources.json` | 如 `li2012` | 原始书目信息、链接、权利状态和访问层级说明 |
| `documents.json` | `inv5875` | 写本身份与研究状态，不假定题名等于作者 |
| `passages.json` | 如 `inv5875-B14-23` | 连续段落或局部定位窗口、字序、译文、坐标及来源 |
| `gaps.json` | `inv5875-G1` | 未释区域及下一步可执行检验 |
| `hypotheses.json` | `inv5875-H1` | 拟释及竞争解释，与字符、义项、未释区连接 |

`sources.json` 的 `redistribution` 是本项目的处理策略，不能代替源文件许可；`reference_only` 表示不分发其全文或图像。`senses.json` 的英文短释是项目辅助译法，不代表字典原作者的英文译文。

每条 `evidence` 包含来源 ID、精确 `locator`、材料类型 `kind`、核对层级 `inspection` 及实际核对日期。日期不是网站发布时间。图像坐标使用左上角原点，矩形 `[left, top, right, bottom)`，尺寸与 `image_reference` 必须对应；不同裁切或缩放图像不能共用坐标。

区分 `null`（没有译文）与文字内容，不以空字符串、问号或模型生成的句子伪装已译。转录扩展与原笔迹不同，例如一个字加重文符可能对应两个排印字；定位窗口不等于字形分割。

## 编号与检索

字符主键直接来自 Unicode 码位。词条与义项 ID 一经发布不复用；本版单字词条采用码位作可读初始编号，新多字词可用稳定的 ASCII ID。引用格式统一为 `[A-Za-z0-9_-]+`，便于 CLDF 等格式使用。

`L4267` 检索简写只展开为 `L2008-4267`。李氏其他版本号、韩序号、Unicode 码位不能因数字接近而自动合并。原出处中明确标记版本的编号继续原样保存。

## CLDF 导出

使用 [CLDF Dictionary](https://github.com/cldf/cldf/tree/master/modules/Dictionary) 的 `EntryTable`、`SenseTable` 与 `LanguageTable`，通过 pycldf 构造元数据、外键和 BibTeX 来源并执行验证。

| 本项目 | CLDF |
| --- | --- |
| 词条 ID、字形、词性 | `EntryTable.ID / Headword / Part_Of_Speech` |
| 唐古特语 | `LanguageTable`：`txg`，ISO 639-3 `txg` |
| 义项 ID、词条 ID、中文短释 | `SenseTable.ID / Entry_ID / Description` |
| 来源及页码 | `Source`，引用随包 `sources.bib` |
| 证据状态、独立复核数 | 扩展列 `Evidence_Status / Independent_Review_Count` |

导出仅选择 `source_checked` 义项，并保留状态说明；字符索引、转录层义项、未释区及假说在原生 JSON 中保留。该导出是一个明确收窄的词典视图，不能用它反推其他记录不存在。音系、方言、语料例句和 TEI/IIIF 尚未实现，不能声称已经兼容这些完整工作流。
