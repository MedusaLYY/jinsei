"""Tests for the canon source parser (header detection, units, scenes, chunks)."""

from __future__ import annotations

import hashlib

import pytest

from overlord_worldsim.canon.model import UnitKind
from overlord_worldsim.canon.parse import (
    PARSED_ARTIFACT_VERSION,
    parse_header_line,
    parse_source,
)


class TestHeaderLine:
    def test_main_header_prologue(self) -> None:
        header = parse_header_line("第一卷 幼年期 序章")
        assert header is not None
        assert header.volume_no == 1
        assert header.period == "幼年期"
        assert header.kind is UnitKind.PROLOGUE
        assert header.title == "序章"
        assert header.part_title is None
        assert header.is_tail is False

    def test_main_header_story(self) -> None:
        header = parse_header_line("第一卷 幼年期 第一话「难道是：异世界」")
        assert header is not None
        assert header.volume_no == 1
        assert header.kind is UnitKind.STORY
        assert header.title == "第一话「难道是：异世界」"

    def test_main_header_side_story(self) -> None:
        header = parse_header_line("第二卷 少年期 家庭教师篇 闲话「后日谈与伯雷亚斯式问候」")
        assert header is not None
        assert header.volume_no == 2
        assert header.period == "少年期"
        assert header.part_title == "家庭教师篇"
        assert header.kind is UnitKind.SIDE
        assert header.title == "闲话「后日谈与伯雷亚斯式问候」"

    def test_main_header_gaiden_no_part_title(self) -> None:
        header = parse_header_line("第一卷 幼年期 外传 格雷拉特家的母亲")
        assert header is not None
        assert header.kind is UnitKind.GAIDEN
        assert header.part_title is None
        assert header.title == "外传 格雷拉特家的母亲"

    def test_main_header_bonus_with_merchant_prefix(self) -> None:
        header = parse_header_line("第一卷 幼年期 蜜瓜特典『透过缝隙守望孩子们的未来』")
        assert header is not None
        assert header.kind is UnitKind.BONUS
        assert header.title == "蜜瓜特典『透过缝隙守望孩子们的未来』"

    def test_main_header_bonus_ascii_prefix(self) -> None:
        header = parse_header_line("第二十六卷 青年期 决定胜负篇&完结篇 Gamers特典 聊聊基斯的事")
        assert header is not None
        assert header.kind is UnitKind.BONUS
        assert header.part_title == "决定胜负篇&完结篇"

    def test_main_header_bonus_zero_width_artifact(self) -> None:
        header = parse_header_line("第三卷 少年期 冒险者入门篇 &#8203;&#8203;特典 比基尼型铠甲")
        assert header is not None
        assert header.kind is UnitKind.BONUS
        assert "\u200b" not in header.title
        assert header.title == "特典 比基尼型铠甲"

    def test_main_header_illustration(self) -> None:
        header = parse_header_line("第一卷 幼年期 插图")
        assert header is not None
        assert header.kind is UnitKind.ILLUSTRATION

    def test_main_header_afterword(self) -> None:
        header = parse_header_line("第一卷 幼年期 后记")
        assert header is not None
        assert header.kind is UnitKind.AFTERWORD
        assert header.in_universe is False

    def test_main_header_bracketed_afterword(self) -> None:
        header = parse_header_line(
            "第二十六卷 青年期 决定胜负篇&完结篇 「后记」（节录自鲁迪乌斯之书第二十六集）"
        )
        assert header is not None
        assert header.kind is UnitKind.AFTERWORD
        assert header.in_universe is False

    def test_main_header_nested_final_chapter(self) -> None:
        header = parse_header_line(
            "第二十六卷 青年期 决定胜负篇&完结篇 最终章 完结篇 第一话「最后的梦」"
        )
        assert header is not None
        assert header.kind is UnitKind.EPILOGUE
        assert header.title == "最终章 完结篇 第一话「最后的梦」"

    def test_main_header_finale(self) -> None:
        header = parse_header_line("第二十六卷 青年期 决定胜负篇&完结篇 最终话「死后的世界」")
        assert header is not None
        assert header.kind is UnitKind.FINALE

    def test_main_header_vol23_has_no_part_title(self) -> None:
        header = parse_header_line("第二十三卷 青年期 第一话「绿色婴孩」")
        assert header is not None
        assert header.volume_no == 23
        assert header.part_title is None
        assert header.kind is UnitKind.STORY

    def test_main_header_vol8_prologue_with_title(self) -> None:
        header = parse_header_line("第八卷 青少年期 学园篇 前 序章「泥沼的冒险者」")
        assert header is not None
        assert header.kind is UnitKind.PROLOGUE
        assert header.part_title == "学园篇 前"

    def test_tail_bonus_short_story(self) -> None:
        header = parse_header_line("短篇 广播剧特典 莉莉娅篇 骑士侍从最初的工作")
        assert header is not None
        assert header.is_tail is True
        assert header.volume_no is None
        assert header.kind is UnitKind.BONUS

    def test_tail_bd_bonus(self) -> None:
        header = parse_header_line("第二季BD特典 BD1 狂犬来过了")
        assert header is not None
        assert header.is_tail is True
        assert header.kind is UnitKind.BONUS

    def test_tail_bare_chapter_heading(self) -> None:
        header = parse_header_line("第一章")
        assert header is not None
        assert header.is_tail is True
        assert header.kind is UnitKind.CHAPTER

    def test_tail_special_book(self) -> None:
        header = parse_header_line("Special book 长篇访谈")
        assert header is not None
        assert header.is_tail is True
        assert header.kind is UnitKind.BONUS
        assert header.in_universe is False

    def test_tail_paul_gaiden(self) -> None:
        header = parse_header_line("保罗外传 冒险者隐退篇 第一话【简妮斯】")
        assert header is not None
        assert header.is_tail is True
        assert header.kind is UnitKind.GAIDEN

    @pytest.mark.parametrize(
        "line",
        [
            "第1卷时我们聊了诞生时的秘话。",
            "第5卷，是以无职转生主旨之一的“不再重蹈前世的覆辙”，",
            "第18卷。感觉很厉害呢。真的是好不容易写到了这里的感觉。",
            "    轻小说文库(Www.WenKu8.Com)",
            "    网译版",
            "    翻译：花団子",
            "    著：长月达平",
            "    转自 B站（https://www.bilibili.com/read/cv27758066/）",
            "★☆★☆★☆轻小说文库(Www.WenKu8.Com)☆★☆★☆★",
            "◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆◇◆",
            "<无职转生～到了异世界就拿出真本事～(无职转生~在异世界认真地活下去~)>",
            "更多精彩热门日本轻小说、动漫小说，尽在轻小说文库(Www.WenKu8.Com)",
            "    那一天，莉莉雅身为剑士的生命就此告终。",
        ],
    )
    def test_rejects_non_header_lines(self, line: str) -> None:
        assert parse_header_line(line) is None


CORPUS = (
    "★☆★☆★☆轻小说文库(Www.WenKu8.Com)☆★☆★☆★\n"
    "\n"
    "<无职转生～到了异世界就拿出真本事～(无职转生~在异世界认真地活下去~)>\n"
    "\n"
    "\n"
    "第一卷 幼年期 序章\n"
    "\n"
    "    第一段正文。\n"
    "\n"
    "    第二段正文。\n"
    "\n"
    "第一卷 幼年期 第一话「测试章节」\n"
    "\n"
    "    正文一。\n"
    "\n"
    "    ※\n"
    "\n"
    "    正文二。\n"
    "\n"
    "第一卷 幼年期 插图\n"
    "\n"
    "短篇 广播剧特典 样例短篇\n"
    "\n"
    "    网译版\n"
    "\n"
    "    翻译：某人\n"
    "\n"
    "    尾巴第一段。\n"
    "\n"
    "    尾巴第二段。\n"
    "\n"
    "更多精彩热门日本轻小说、动漫小说，尽在轻小说文库(Www.WenKu8.Com)\n"
)


class TestParseSource:
    def test_deterministic_ids_and_line_ranges(self) -> None:
        first = parse_source(CORPUS)
        second = parse_source(CORPUS)
        assert first == second
        assert [u.unit_id for u in first.units] == [u.unit_id for u in second.units]
        assert [c.chunk_id for c in first.chunks] == [c.chunk_id for c in second.chunks]

    def test_units_and_volumes(self) -> None:
        doc = parse_source(CORPUS)
        assert len(doc.volumes) == 1
        assert doc.volumes[0].volume_no == 1
        assert doc.volumes[0].title == "第一卷 幼年期"
        assert doc.volumes[0].period == "幼年期"
        assert len(doc.units) == 4
        unit_ids = [u.unit_id for u in doc.units]
        assert unit_ids == ["U0001", "U0002", "U0003", "U0004"]
        prologue = doc.units[0]
        assert prologue.start_line == 6
        assert prologue.end_line == 11
        assert prologue.kind is UnitKind.PROLOGUE
        assert prologue.in_universe is True
        story = doc.units[1]
        assert story.start_line == 12
        assert story.end_line == 19
        illustration = doc.units[2]
        assert illustration.kind is UnitKind.ILLUSTRATION
        assert illustration.char_count == 0
        assert illustration.paragraph_count == 0
        tail = doc.units[3]
        assert tail.kind is UnitKind.BONUS
        assert tail.volume_no is None
        assert tail.canon_layer == "UNKNOWN"
        assert tail.start_line == 22
        assert tail.end_line == 30

    def test_skipped_lines(self) -> None:
        doc = parse_source(CORPUS)
        skipped = {s.line_no: s.reason for s in doc.skipped}
        assert skipped[1] == "banner"
        assert skipped[3] == "file_title"
        assert skipped[24] == "unit_metadata"
        assert skipped[26] == "unit_metadata"
        assert skipped[32] == "banner"

    def test_scenes_and_break_markers(self) -> None:
        doc = parse_source(CORPUS)
        story_scenes = [s for s in doc.scenes if s.unit_id == "U0002"]
        assert len(story_scenes) == 2
        assert story_scenes[0].break_line is None
        assert story_scenes[1].break_line == 16

    def test_chunks_never_cross_scene_or_paragraph(self) -> None:
        doc = parse_source(CORPUS)
        scenes_by_unit = {
            u.unit_id: [s.scene_id for s in doc.scenes if s.unit_id == u.unit_id] for u in doc.units
        }
        for chunk in doc.chunks:
            assert chunk.scene_id in scenes_by_unit[chunk.unit_id]
            assert chunk.source_start_line <= chunk.source_end_line
            assert chunk.text.count("\n") + 1 == len(chunk.paragraph_lines)

    def test_chunk_fields(self) -> None:
        doc = parse_source(CORPUS)
        first = next(c for c in doc.chunks if c.unit_id == "U0001")
        assert first.chunk_id == "C000001"
        assert first.chapter_title == "序章"
        assert first.text == "第一段正文。\n第二段正文。"
        assert first.paragraph_lines == (8, 10)
        assert first.source_start_line == 8
        assert first.source_end_line == 10
        assert first.sha256 == hashlib.sha256("第一段正文。\n第二段正文。".encode()).hexdigest()

    def test_tail_metadata_lines_not_paragraphs(self) -> None:
        doc = parse_source(CORPUS)
        tail = doc.units[3]
        assert tail.paragraph_count == 2
        assert tail.char_count == 12


class TestParsedDocumentJson:
    def test_can_serialize_all_artifacts(self) -> None:
        doc = parse_source(CORPUS)
        assert doc.to_volumes_json()["version"] == PARSED_ARTIFACT_VERSION
        assert len(doc.to_units_json()["units"]) == 4
        scenes = doc.to_scenes_jsonl()
        assert len(scenes) == 4
        chunks = doc.to_chunks_jsonl()
        assert len(chunks) == 4
        report = doc.to_report_jsonl()
        assert len(report) == 5
