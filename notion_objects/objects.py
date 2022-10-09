import inspect
from datetime import datetime
from typing import ClassVar, List

from .properties import Properties, Property, RootProperty


class NotionClass(type):
    __properties__: List[Property]

    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)

        # build property list
        properties = []
        for b in bases:
            # get inherited properties
            properties.extend([a for a in getattr(b, "properties", []) if isinstance(a, Property)])
        # inspect the current class for properties
        properties = [
            prop for _, prop in inspect.getmembers(new_cls, lambda m: isinstance(m, Property))
        ]
        new_cls.__properties__ = properties
        return new_cls


class NotionObject(metaclass=NotionClass):
    __properties__: ClassVar[List[Property]]

    _obj: dict

    def __init__(self, obj):
        self._obj = obj

    def to_dict(self):
        result = {}

        for prop in self.__properties__:
            result[prop.attr] = getattr(self, prop.attr)

        return result


class DynamicNotionObject:
    _properties: Properties
    _obj: dict

    def __init__(self, obj: dict):
        self._obj = obj
        self._properties = Properties.parse(obj)

    def to_dict(self):
        result = {}

        for prop in self._properties:
            result[prop.attr] = prop.get(prop.field, self._obj)

        return result


class Page(NotionObject):
    id: str = RootProperty("id")
    created_time: datetime = RootProperty()
    last_edited_time: datetime = RootProperty()
