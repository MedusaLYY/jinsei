"""Edge-case tests for the canon parser (branch coverage)."""

from __future__ import annotations

from overlord_worldsim.canon.parse import (
    _cn_numeral,
    parse_header_line,
    parse_source,
)


def test_cn_numeral_numeric_and_hundreds() -> None:
    assert _cn_numeral("1") == 1
    assert _cn_numeral("一百") == 100
    assert _cn_numeral("一百二十") == 120
    assert _cn_numeral("二十") == 20
    assert _cn_numeral("十") == 10


def test_header_numeric_volume() -> None:
    header = parse_header_line("第1卷 幼年期 序章")
    assert header is not None
    assert header.volume_no == 1
    assert header.period == "幼年期"
    assert header.title == "序章"


def test_tail_unit_kind_via_substring() -> None:
    doc = parse_source("主线漫画特典 某标题\n\n    内容。\n")
    unit = doc.units[0]
    assert unit.kind.value == "BONUS"
    assert unit.canon_layer == "UNKNOWN"


def test_tail_unit_kind_substring_without_prefix() -> None:
    doc = parse_source("第三特典 番外一篇\n\n    内容。\n")
    assert doc.units[0].kind.value == "BONUS"


def test_tail_unit_unknown_kind_fallback() -> None:
    doc = parse_source("神秘番外 无题\n\n    内容。\n")
    assert doc.units == []
    skipped = [s for s in doc.skipped if s.reason == "unknown_heading"]
    assert len(skipped) == 1
    assert skipped[0].text == "神秘番外 无题"


def test_unknown_heading_skipped() -> None:
    doc = parse_source("第一卷 幼年期 序章\n\n    正文。\n\n这是没有头的行\n\n    后续。\n")
    skipped = [s for s in doc.skipped if s.reason == "unknown_heading"]
    assert len(skipped) == 1
    assert skipped[0].text == "这是没有头的行"
    assert doc.units[0].end_line == 3
    assert any(s.reason == "orphan_body" for s in doc.skipped)


def test_orphan_body_skipped() -> None:
    doc = parse_source("    无头的正文行。\n")
    skipped = [s for s in doc.skipped if s.reason == "orphan_body"]
    assert len(skipped) == 1
    assert doc.units == []


def test_orphan_body_resets_at_banner() -> None:
    doc = parse_source(
        "★☆★☆轻小说文库(Www.WenKu8.Com)☆★☆★\n    孤行。\n第一卷 幼年期 序章\n\n    正文。\n"
    )
    assert doc.units[0].start_line == 3
    assert doc.units[0].paragraph_count == 1
