from typing import Literal, Optional

RichTextType = Literal[
    "text",
    "mention",
    "equation",
]

Color = Literal[
    "default",
    "blue",
    "blue_background",
    "brown",
    "brown_background",
    "default",
    "gray",
    "gray_background",
    "green",
    "green_background",
    "orange",
    "orange_background",
    "pink",
    "pink_background",
    "purple",
    "purple_background",
    "red",
    "red_background",
    "yellow",
    "yellow_background",
]

MentionType = Literal[
    "database",
    "date",
    "link_preview",
    "page",
    "template_mention",
    "user",
]


class RichTextObject:
    """
    A RichText block. See https://developers.notion.com/reference/rich-text.

    An example of a RichText object::
        {
          "type": "text",
          "text": {
            "content": "Some words ",
            "link": null
          },
          "annotations": {
            "bold": false,
            "italic": false,
            "strikethrough": false,
            "underline": false,
            "code": false,
            "color": "default"
          },
          "plain_text": "Some words ",
          "href": null
        }
    """

    type: RichTextType

    href: Optional[str]

    # annotations
    bold: bool
    italic: bool
    strikethrough: bool
    underline: bool
    code: bool
    color: Color

    def __init__(
        self,
        *,
        href: Optional[str] = None,
        bold: bool = False,
        italic: bool = False,
        strikethrough: bool = False,
        underline: bool = False,
        code: bool = False,
        color: Color = "default",
    ):
        self.href = href
        self.bold = bold
        self.italic = italic
        self.strikethrough = strikethrough
        self.underline = underline
        self.code = code
        self.color = color

    @property
    def plain_text(self):
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            f"{self.type}": {},
            "annotations": {
                "bold": self.bold,
                "italic": self.italic,
                "strikethrough": self.strikethrough,
                "underline": self.underline,
                "code": self.code,
                "color": self.color,
            },
            "plain_text": self.plain_text,
            "href": self.href,
        }

    def __repr__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()


class RichText(RichTextObject):
    type = "text"

    content: str
    link: Optional[str] = None

    def __init__(self, content: str, link: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.link = link
        self.href = kwargs.get("href", link)

    @property
    def plain_text(self):
        return self.content

    def to_dict(self) -> dict:
        base = super().to_dict()
        base[self.type] = {
            "content": self.content,
            "link": None if not self.link else {"url": self.link},
        }
        return base


class Link(RichText):
    def __init__(self, link: str, content: str = None, **kwargs):
        if content is None:
            content = link
        super().__init__(content=content, link=link, **kwargs)


class Equation(RichTextObject):
    """
    Contains a RichTextBase and the following content block::

      {
          "equation": {
            "expression": "E = mc^2"
          }
          "plain_text": "E = mc^2",
          ...
      }

    """

    type = "equation"
    expression: str

    def __init__(self, expression: str, **kwargs):
        super().__init__(**kwargs)
        self.expression = expression

    @property
    def plain_text(self):
        return self.expression

    def to_dict(self) -> dict:
        base = super().to_dict()
        base[self.type] = {
            "expression": self.expression,
        }
        return base


class Mention(RichTextObject):
    # TODO implement Mention

    type = "mention"
    mention_type: MentionType

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError


def parse(doc: dict) -> RichTextObject:
    try:
        type = doc["type"]
        kwargs = {
            "href": doc.get("href"),
            # flatten annotations
            **doc.get("annotations", {}),
        }

        if type == "text":
            factory = RichText
            # flatten content type
            kwargs["content"] = doc[type]["content"]
            kwargs["link"] = (doc[type].get("link") or {}).get("url")
        elif type == "equation":
            factory = Equation
            kwargs["expression"] = doc[type]["expression"]
        elif type == "mention":
            factory = Mention
            # TODO
        else:
            raise ValueError(f"Unknown RichText type {type}")

        return factory(**kwargs)

    except (KeyError, TypeError) as e:
        raise ValueError(f"Error parsing RichText object: {e}") from e
