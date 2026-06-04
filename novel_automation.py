#!/usr/bin/env python3
"""A lightweight Chinese novel creation assistant.

This script intentionally uses deterministic templates instead of external AI
services, so it works offline and is easy to customize. It can create a full
novel package: premise, synopsis, outline, characters, worldbuilding, chapter
plots, draft text, and a simple proofreading report.
"""
from __future__ import annotations

import argparse
import json
import re
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


GENRE_SETTINGS = {
    "玄幻": {
        "world": "灵气复苏后的九州大陆，宗门、古城与秘境彼此牵制",
        "power": "以心法、灵器、契约兽和悟道境界推动成长",
        "conflict": "远古封印松动，主角必须在宗门纷争与天下大义之间做选择",
    },
    "都市": {
        "world": "高速变化的现代都市，资本、家庭与梦想互相拉扯",
        "power": "依靠专业能力、人脉资源、信息差和个人信念破局",
        "conflict": "看似普通的职场或生活事件，逐步牵出更大的利益漩涡",
    },
    "科幻": {
        "world": "近未来星际社会，人工智能、殖民星和地球旧秩序并存",
        "power": "通过科技装备、算法推演、舰队协作和科学探索推进情节",
        "conflict": "一次异常信号暴露文明危机，主角被迫承担跨星系抉择",
    },
    "悬疑": {
        "world": "表面平静的小城或封闭空间，人人都隐藏着不可告人的秘密",
        "power": "凭借观察、推理、证据链和心理博弈层层逼近真相",
        "conflict": "旧案与新案交叠，真相越接近，主角越可能失去最珍贵的东西",
    },
    "言情": {
        "world": "现实与理想交错的情感场域，事业、亲情和自我成长同等重要",
        "power": "通过沟通、选择、误会化解和双向成长推动关系升温",
        "conflict": "两位主角因目标相悖而靠近，又因真实需求而重新理解彼此",
    },
}

ARC_BEATS = [
    "开端：展示主角日常、核心缺憾和即将被打破的平衡。",
    "诱因：突发事件迫使主角离开舒适区，提出全书核心问题。",
    "探索：主角尝试解决问题，结识盟友，也暴露能力短板。",
    "升级：反派或阻力显形，代价增加，主角第一次重大失败。",
    "中点：主角获得关键线索或力量，但发现真相比想象更危险。",
    "低谷：信任崩塌、计划失败或重要人物离去，主角面对内心弱点。",
    "反击：主角整合资源，做出不可逆选择，主动挑战最终阻力。",
    "高潮：核心矛盾集中爆发，主角用成长后的方式解决问题。",
    "余波：交代人物去向、主题回响，并留下续作钩子或情感余韵。",
]

COMMON_TYPOS = {
    "的地得": "请根据语境拆分“的 / 地 / 得”。",
    "既然...就": "检查关联词是否完整：既然……就……。",
    "虽然...但是": "检查转折关系是否清晰：虽然……但是……。",
    "在在": "疑似重复用词。",
    "了了": "疑似重复用词。",
    "是是": "疑似重复用词。",
}


@dataclass
class Character:
    name: str
    role: str
    desire: str
    weakness: str
    arc: str


@dataclass
class Chapter:
    index: int
    title: str
    purpose: str
    conflict: str
    cliffhanger: str
    draft: str = ""


@dataclass
class NovelProject:
    title: str
    genre: str
    theme: str
    audience: str
    logline: str
    synopsis: str
    selling_points: list[str]
    worldbuilding: dict[str, str]
    characters: list[Character]
    outline: list[str]
    chapters: list[Chapter]
    proofreading: list[str] = field(default_factory=list)


class NovelAutomator:
    """Generate a complete, editable novel planning package."""

    def __init__(self, title: str, genre: str, protagonist: str, theme: str, chapters: int):
        if chapters < 1:
            raise ValueError("chapters must be at least 1")
        self.title = title.strip() or "未命名小说"
        self.genre = genre.strip() or "都市"
        self.protagonist = protagonist.strip() or "林澈"
        self.theme = theme.strip() or "在困境中找回真正的自我"
        self.chapter_count = chapters
        self.setting = GENRE_SETTINGS.get(self.genre, GENRE_SETTINGS["都市"])

    def build_project(self, include_draft: bool = True) -> NovelProject:
        characters = self._characters()
        outline = self._outline()
        chapters = self._chapters(outline, include_draft=include_draft)
        synopsis = self._synopsis(characters)
        project = NovelProject(
            title=self.title,
            genre=self.genre,
            theme=self.theme,
            audience=self._audience(),
            logline=self._logline(),
            synopsis=synopsis,
            selling_points=self._selling_points(),
            worldbuilding=self._worldbuilding(),
            characters=characters,
            outline=outline,
            chapters=chapters,
        )
        project.proofreading = proofread_text(self._project_text(project))
        return project

    def _audience(self) -> str:
        return f"喜欢{self.genre}题材、强情节推进、人物成长和阶段性爽点的网络小说读者。"

    def _logline(self) -> str:
        return (
            f"{self.protagonist}在{self.setting['world']}中卷入危机，"
            f"必须借助{self.setting['power']}，完成“{self.theme}”的成长命题。"
        )

    def _selling_points(self) -> list[str]:
        return [
            f"类型承诺明确：以{self.genre}读者熟悉的期待开局，并持续升级冲突。",
            "创作资料完整：从一句话卖点到章节正文草稿均可继续扩写。",
            "人物弧光清晰：主角目标、缺陷、失败和最终选择互相呼应。",
            "可校对迭代：内置基础校对报告，便于发现重复、长句和标点问题。",
        ]

    def _worldbuilding(self) -> dict[str, str]:
        return {
            "时代与舞台": self.setting["world"],
            "核心规则": self.setting["power"],
            "主要矛盾": self.setting["conflict"],
            "主题表达": self.theme,
            "可扩展素材": "重要地名、组织关系、道具规则、历史传说和禁忌代价。",
        }

    def _characters(self) -> list[Character]:
        return [
            Character(
                name=self.protagonist,
                role="主角",
                desire="证明自己有能力改变命运，并保护重要的人。",
                weakness="习惯独自承担，害怕暴露脆弱，因此常错过求助时机。",
                arc="从被动卷入到主动选择，学会把个人执念转化为更成熟的责任。",
            ),
            Character(
                name="沈砚",
                role="盟友 / 镜像人物",
                desire="追查隐藏在危机背后的真相。",
                weakness="过度理性，不愿相信直觉和情感价值。",
                arc="在与主角合作中理解信任，成为最终反击的重要支点。",
            ),
            Character(
                name="顾无咎",
                role="主要对手",
                desire="用极端方式重塑秩序，证明自己的道路才是唯一答案。",
                weakness="无法接受失控，越追求完美越制造更大的破绽。",
                arc="从幕后操盘者走到台前，与主角在价值观上正面碰撞。",
            ),
            Character(
                name="阿岚",
                role="情感锚点 / 信息提供者",
                desire="守住普通人的生活，不再被大人物的棋局牺牲。",
                weakness="害怕改变，常把希望寄托在别人身上。",
                arc="从等待拯救到主动参与，帮助主角看见事件的人性代价。",
            ),
        ]

    def _outline(self) -> list[str]:
        return [f"{beat} 对应主题：{self.theme}" for beat in ARC_BEATS]

    def _chapters(self, outline: list[str], include_draft: bool) -> list[Chapter]:
        chapters: list[Chapter] = []
        for index in range(1, self.chapter_count + 1):
            beat = outline[min((index - 1) * len(outline) // self.chapter_count, len(outline) - 1)]
            title = f"第{index}章：{self._chapter_title(index)}"
            purpose = f"承接结构节点“{beat.split('：', 1)[0]}”，推进主角对危机的理解。"
            conflict = self._chapter_conflict(index)
            cliffhanger = self._cliffhanger(index)
            draft = self._draft_chapter(index, title, purpose, conflict, cliffhanger) if include_draft else ""
            chapters.append(Chapter(index, title, purpose, conflict, cliffhanger, draft))
        return chapters

    def _chapter_title(self, index: int) -> str:
        titles = ["平衡破裂", "意外来信", "第一条线索", "旧友重逢", "暗处的眼睛", "代价浮现", "反击计划", "真相之门", "最后选择"]
        return titles[(index - 1) % len(titles)]

    def _chapter_conflict(self, index: int) -> str:
        scale = "个人困境" if index <= max(1, self.chapter_count // 3) else "外部压迫" if index <= max(2, self.chapter_count * 2 // 3) else "价值抉择"
        return f"本章冲突层级为{scale}：{self.protagonist}必须在安全选择与冒险推进之间做决定。"

    def _cliffhanger(self, index: int) -> str:
        if index == self.chapter_count:
            return "危机暂时解除，但新的线索表明更大的故事才刚开始。"
        return f"结尾抛出第{index + 1}章问题：关键证据为何会指向主角最信任的人？"

    def _synopsis(self, characters: list[Character]) -> str:
        ally = characters[1].name
        villain = characters[2].name
        return (
            f"《{self.title}》是一部{self.genre}小说。{self.protagonist}原本只想过平静生活，"
            f"却因一次异常事件被卷入{self.setting['conflict']}。在{ally}的协助下，"
            f"主角逐渐发现事件背后隐藏着{villain}的计划。随着线索深入，主角必须面对自身缺陷，"
            f"并在亲情、友情、理想与代价之间做出选择。最终，主角以新的方式理解“{self.theme}”，"
            "完成个人成长，也为下一阶段的更大危机埋下伏笔。"
        )

    def _draft_chapter(self, index: int, title: str, purpose: str, conflict: str, cliffhanger: str) -> str:
        paragraphs = [
            f"{title}\n",
            f"清晨的风带着一点不合时宜的冷意，{self.protagonist}站在熟悉的街口，却第一次觉得这座城市如此陌生。",
            f"昨夜留下的线索像一根细针，扎在他心里。{purpose} 他知道自己可以假装什么都没有发生，但那样一来，所有答案都会被黑暗吞没。",
            f"{conflict} 当沈砚把新的证据推到他面前时，屋子里安静得只剩钟声。证据并不完整，却足够证明有人在暗中引导他们。",
            f"阿岚低声提醒他：真正危险的不是敌人有多强，而是你愿不愿意承认自己也会害怕。{self.protagonist}沉默很久，终于把那份证据收进口袋。",
            f"他决定继续追查。门外的脚步声忽然停住，像有什么人已经等候多时。{cliffhanger}",
        ]
        return "\n\n".join(paragraphs)

    def _project_text(self, project: NovelProject) -> str:
        return "\n".join(
            [project.logline, project.synopsis, *project.outline, *[chapter.draft for chapter in project.chapters]]
        )


def proofread_text(text: str) -> list[str]:
    """Return lightweight proofreading suggestions for Chinese prose."""
    suggestions: list[str] = []
    if not text.strip():
        return ["文本为空：请先生成或输入正文。"]

    for typo, message in COMMON_TYPOS.items():
        if typo in text:
            suggestions.append(f"发现“{typo}”：{message}")

    repeated = sorted(set(re.findall(r"([\u4e00-\u9fff]{2,})\1", text)))
    for word in repeated[:5]:
        suggestions.append(f"疑似连续重复词：{word}{word}。")

    long_sentences = [sentence for sentence in re.split(r"[。！？!?]", text) if len(sentence) > 90]
    if long_sentences:
        suggestions.append(f"发现 {len(long_sentences)} 个超过 90 字的长句，建议拆分以增强节奏。")

    if text.count("“") != text.count("”"):
        suggestions.append("中文引号数量不匹配，请检查对话或引用。")
    if text.count("（") != text.count("）"):
        suggestions.append("中文括号数量不匹配，请检查补充说明。")

    adverbs = ["突然", "立刻", "马上", "非常", "极其"]
    overused = {word: text.count(word) for word in adverbs if text.count(word) >= 4}
    for word, count in overused.items():
        suggestions.append(f"“{word}”出现 {count} 次，建议替换部分表达。")

    return suggestions or ["未发现明显问题。建议继续人工检查人物动机、伏笔回收和章节节奏。"]


def project_to_markdown(project: NovelProject) -> str:
    character_lines = "\n".join(
        f"- **{c.name}（{c.role}）**：目标：{c.desire} 缺陷：{c.weakness} 弧光：{c.arc}"
        for c in project.characters
    )
    outline_lines = "\n".join(f"{i}. {item}" for i, item in enumerate(project.outline, start=1))
    chapter_lines = "\n\n".join(
        textwrap.dedent(
            f"""
            ### {chapter.title}
            - 功能：{chapter.purpose}
            - 冲突：{chapter.conflict}
            - 钩子：{chapter.cliffhanger}

            {chapter.draft or '_未生成正文草稿_'}
            """
        ).strip()
        for chapter in project.chapters
    )
    proofreading_lines = "\n".join(f"- {item}" for item in project.proofreading)
    selling_points = "\n".join(f"- {item}" for item in project.selling_points)
    world_lines = "\n".join(f"- **{key}**：{value}" for key, value in project.worldbuilding.items())

    return textwrap.dedent(
        f"""
        # {project.title}

        ## 基础设定
        - 类型：{project.genre}
        - 主题：{project.theme}
        - 目标读者：{project.audience}
        - 一句话卖点：{project.logline}

        ## 简介
        {project.synopsis}

        ## 卖点
        {selling_points}

        ## 世界观 / 背景
        {world_lines}

        ## 主要人物
        {character_lines}

        ## 剧情大纲
        {outline_lines}

        ## 分章剧情与正文草稿
        {chapter_lines}

        ## 校对报告
        {proofreading_lines}
        """
    ).strip() + "\n"


def project_to_json(project: NovelProject) -> str:
    return json.dumps(asdict(project), ensure_ascii=False, indent=2)


def write_output(content: str, output: Path | None) -> None:
    if output is None:
        print(content)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"已写入：{output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成小说大纲、剧情、简介、正文草稿并进行基础校对。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="生成完整小说创作包")
    generate.add_argument("--title", default="星河尽头的来信", help="小说标题")
    generate.add_argument("--genre", default="都市", choices=sorted(GENRE_SETTINGS), help="小说类型")
    generate.add_argument("--protagonist", default="林澈", help="主角姓名")
    generate.add_argument("--theme", default="在困境中找回真正的自我", help="主题表达")
    generate.add_argument("--chapters", type=int, default=6, help="生成章节数量")
    generate.add_argument("--format", choices=["markdown", "json"], default="markdown", help="输出格式")
    generate.add_argument("--no-draft", action="store_true", help="只生成规划，不生成正文草稿")
    generate.add_argument("--output", type=Path, help="输出文件路径；不填则打印到终端")

    proofread = subparsers.add_parser("proofread", help="校对已有正文文本")
    proofread.add_argument("input", type=Path, help="待校对文本文件")
    proofread.add_argument("--output", type=Path, help="校对报告输出路径；不填则打印到终端")
    return parser


def run_generate(args: argparse.Namespace) -> None:
    automator = NovelAutomator(args.title, args.genre, args.protagonist, args.theme, args.chapters)
    project = automator.build_project(include_draft=not args.no_draft)
    content = project_to_json(project) if args.format == "json" else project_to_markdown(project)
    write_output(content, args.output)


def run_proofread(args: argparse.Namespace) -> None:
    text = args.input.read_text(encoding="utf-8")
    report = "\n".join(f"- {item}" for item in proofread_text(text)) + "\n"
    write_output(report, args.output)


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "generate":
        run_generate(args)
    elif args.command == "proofread":
        run_proofread(args)
    else:  # pragma: no cover - argparse prevents this branch
        parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
