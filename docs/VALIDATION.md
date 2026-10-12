# v0.1.0 验证记录

日期：2026-10-12。软件验证不等于语言学结论经过专家复核。

## 本地已执行

- Python 3.12.14：28项 `unittest` 通过，覆盖检索、字符索引重建、来源和字头外键、状态约束、坐标边界、隐私模式、网页导出和 CLDF 导出。
- JSON Schema 与跨表语义校验通过；Ruff 通过；JavaScript 语法检查通过。
- pycldf 1.43.1 验证导出的 Dictionary；检查词义状态、外键及带定位的来源引用。
- 发布脚本连续生成两次，两份 SHA256 清单逐字相同。此结论针对相同版本的数据和工具环境，不是所有未来依赖版本的可重复性承诺。
- Chromium 154.0.8037.98：25项实际交互断言通过，覆盖字形／编码／字书编号／中英文释义检索，证据定位，范围筛选，分页，未覆盖字体提示，无结果输入，假说链接，研究计数，贡献入口和键盘焦点。
- 1360×1000与390×844视口已检查；手机宽度没有页面横向溢出，选择字头后能定位详情；减少动态效果设置有效。
- 已查看桌面与手机渲染图，检查排版和字形显示；这项检查由 AI 执行，不记作语言学专家审阅。
- 公开文件检查：没有私人文件路径、凭据、整本现代字典、论文 PDF 或扫描图。第三方字体和 Unicode 文件具有独立许可及 SHA256 记录。

## 复现浏览器检查

先按 README 构建并启动本地站点。浏览器检查使用 Playwright CLI，执行时需要 Node.js 与可用浏览器：

```bash
mkdir -p output/playwright
npx --package @playwright/cli playwright-cli -s=tangut open http://127.0.0.1:8000 --headed
npx --package @playwright/cli playwright-cli -s=tangut snapshot
npx --package @playwright/cli playwright-cli -s=tangut run-code --filename=scripts/browser-smoke.js
```

脚本中的固定条目和数量用于首版回归样本。增加词条或改变字体覆盖时，需相应更新首版样本假定，不能只为使测试通过而更改研究数据。

## 发布时的远端验证

GitHub Actions 的 `Checks` 在 Python 3.11和3.13运行数据、代码、导出与构建检查；`Pages` 在部署前再执行必要检查。以对应提交的 [Actions记录](https://github.com/ZJUZhiyuCai/tangut-workbench/actions) 为实际结果。

线上部署后，还应检查首页、数据文件和字典交互。浏览器验证脚本不作为每次 CI 自动浏览器测试执行；CI 当前检查静态脚本语法和生成数据，实际界面变更仍须运行浏览器检查。
