import pytest

from notion_objects import rich_text


def test_parse_text():
    obj = rich_text.parse(
        {
            "type": "text",
            "text": {"content": "Some words ", "link": None},
            "annotations": {
                "bold": True,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "red",
            },
            "plain_text": "Some words ",
            "href": None,
        }
    )

    assert isinstance(obj, rich_text.RichText)
    assert obj.bold
    assert not obj.italic
    assert not obj.strikethrough
    assert not obj.underline
    assert not obj.code
    assert obj.color == "red"

    assert obj.plain_text == "Some words "
    assert obj.content == "Some words "
    assert obj.link is None


def test_rich_text_to_dict():
    obj = rich_text.RichText("Some words ", "https://example.com", color="red", bold=True)

    assert obj.to_dict() == {
        "type": "text",
        "text": {"content": "Some words ", "link": {"url": "https://example.com"}},
        "annotations": {
            "bold": True,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "red",
        },
        "plain_text": "Some words ",
        "href": "https://example.com",
    }


def test_link_to_dict():
    obj = rich_text.Link("https://example.com", bold=True)

    assert obj.to_dict() == {
        "type": "text",
        "text": {
            "content": "https://example.com",
            "link": {"url": "https://example.com"},
        },
        "annotations": {
            "bold": True,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "default",
        },
        "plain_text": "https://example.com",
        "href": "https://example.com",
    }


def test_parse_and_render_partial_text():
    obj = rich_text.parse({"type": "text", "text": {"content": "Some words "}})

    assert isinstance(obj, rich_text.RichText)

    assert obj.to_dict() == {
        "type": "text",
        "text": {"content": "Some words ", "link": None},
        "annotations": {
            "bold": False,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "default",
        },
        "plain_text": "Some words ",
        "href": None,
    }


def test_parse_and_render_partial_equation():
    obj = rich_text.parse({"type": "equation", "equation": {"expression": "E = MC^2"}})

    assert isinstance(obj, rich_text.Equation)

    assert obj.to_dict() == {
        "type": "equation",
        "equation": {
            "expression": "E = MC^2",
        },
        "annotations": {
            "bold": False,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "default",
        },
        "plain_text": "E = MC^2",
        "href": None,
    }


def test_parse_invalid_text():
    doc = {
        "type": "text",
        "text": {
            # missing content
            "link": None,
        },
        "annotations": {
            "bold": True,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "red",
        },
        "plain_text": "Some words ",
        "href": None,
    }

    with pytest.raises(ValueError) as e:
        rich_text.parse(doc)
    e.match("Error parsing RichText object")
