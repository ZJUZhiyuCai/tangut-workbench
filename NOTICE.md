# Rights and provenance / 许可与来源

本仓库采用分层许可。根目录 `LICENSE` 不覆盖所有内容。

| 范围 | 许可／处理方式 |
| --- | --- |
| `src/`、`scripts/`、`tests/`、`web/` 的代码、`schemas/`、工作流与配置 | MIT；Copyright 2026 Tangut Workbench contributors |
| 项目原创研究注释、文档、除字头索引外的 `data/*.json` | CC BY 4.0；Copyright 2026 Tangut Workbench contributors；见 `licenses/CC-BY-4.0.txt` |
| `vendor/unicode/TangutSources-17.0.0.txt` 与据其机械转换的 `data/characters.jsonl` | Unicode License V3；版权声明在原文件与 `licenses/Unicode-3.0.txt` 中保留 |
| `web/assets/NotoSerifTangut-Regular.ttf` | Noto Serif Tangut v2.170 官方发布文件，未修改；Copyright 2022 The Noto Project Authors；SIL OFL 1.1，见 `licenses/OFL-NotoSerifTangut.txt` |
| `vendor/manifest.json` 所列第三方许可证正文 | 原许可文本，保留其本来属性，不以项目许可重授权 |
| 外部字典、论文、古籍版本、馆藏记录、扫描图及链接内容 | 不随本项目分发；各自权利仍属于其权利人 |

`build/site/dataset.json` 是上述数据的组合，不能忽略其中 Unicode 索引的来源。CLDF 导出只包含选出的项目注释和短小事实性释义，随包附 CC BY 4.0；具体义项仍应引用其所据字典。本项目的许可只在贡献者有权授予的范围内生效，不对事实本身、古籍公有领域内容或第三方权利主张独占。

Unicode 原文件只转换为一字一行 JSONL；不增加词义，不推定不同版本字书编号完全相同。转换可离线重现。官方来源、字体发布版本、压缩包内路径和 SHA256 见 `vendor/manifest.json`。

字典原页的少量事实性词义与项目释读意见分别注明来源。现代书籍、作者译文、扫描图和网页聚合数据没有被整体转授 CC BY 4.0。Open Tangut 仓库标注 MIT，但该标注不替代对其采集的第三方内容的单独核查；本版没有复制其数据。

初始研究记录与代码由 AI 辅助整理；没有虚构专家署名、同行评议、机构隶属或原始手稿阅读权限。引用不构成被引作者、Unicode、Noto、CLDF、Dictionaria 或收藏机构的认可。

如发现出处或权利标注问题，请在本仓库提交 Issue，注明文件和记录 ID，以便核查并在修订历史中更正。
