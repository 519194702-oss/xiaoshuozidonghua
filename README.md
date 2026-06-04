# 小说自动化创作助手

这是一个不依赖外部服务的简易小说自动化脚本，可在本地生成创作小说常用素材，并支持正文草稿生成和基础校对。

## 功能

- 生成小说标题、类型、主题、目标读者和一句话卖点
- 生成简介、卖点、世界观 / 背景设定
- 生成主要人物卡（目标、缺陷、人物弧光）
- 生成九段式剧情大纲
- 生成分章剧情、章节冲突、结尾钩子和正文草稿
- 对生成内容或已有正文进行基础校对，提示重复词、长句、标点配对和高频副词等问题
- 支持 Markdown 和 JSON 输出

## 快速开始

```bash
python3 novel_automation.py generate --title "雾城来信" --genre 悬疑 --protagonist 许知远 --chapters 5 --output output/雾城来信.md
```

生成 JSON：

```bash
python3 novel_automation.py generate --format json --output output/novel.json
```

只生成规划，不生成正文草稿：

```bash
python3 novel_automation.py generate --no-draft
```

校对已有正文：

```bash
python3 novel_automation.py proofread path/to/chapter.txt --output output/proofread.md
```

## 支持类型

当前内置类型包括：玄幻、都市、科幻、悬疑、言情。你可以在 `GENRE_SETTINGS` 中继续扩展类型、世界观、力量体系和核心冲突模板。

## 说明

本项目使用规则和模板生成内容，适合快速搭建小说项目雏形。生成结果建议继续人工扩写、调整人物动机，并结合具体风格进行二次润色。
