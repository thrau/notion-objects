import inspect
from datetime import datetime

from .attributes import RootAttribute


class NotionObject:
    _obj: dict

    def __init__(self, obj: dict):
        self._obj = obj

    def to_dict(self):
        notion_attrs = getattr(self, "_notion_attrs_", {})
        result = {}

        for cls in reversed(inspect.getmro(self.__class__)):
            if cls in notion_attrs:
                for attr in notion_attrs[cls]:
                    result[attr.attr] = getattr(self, attr.attr)

        return result


class Page(NotionObject):
    id: str = RootAttribute("id")
    created_time: datetime = RootAttribute()
    last_edited_time: datetime = RootAttribute()
