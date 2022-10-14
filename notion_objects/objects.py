import inspect
import json
from datetime import datetime
from typing import Iterable, List

from .encode import JSONEncoder
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


class _ConverterMixin:
    def to_dict(self) -> dict:
        result = {}

        for prop in self._get_properties():
            result[prop.attr] = getattr(self, prop.attr)

        return result

    def to_json(self):
        return json.dumps(self.to_dict(), cls=JSONEncoder)

    def _get_properties(self) -> Iterable[Property]:
        raise NotImplementedError


class NotionObject(_ConverterMixin, metaclass=NotionClass):
    _obj: dict

    def __init__(self, obj):
        self._obj = obj

    def _get_properties(self) -> Iterable[Property]:
        return self.__properties__


class DynamicNotionObject(_ConverterMixin):
    _properties: Properties
    _obj: dict

    def __init__(self, obj: dict, properties: Properties = None):
        self._obj = obj
        self._properties = properties or Properties.parse(obj)
        self._properties_by_attr = {prop.attr: prop for prop in self._properties}

    def __getattr__(self, item):
        try:
            if item in self._properties_by_attr:
                prop = self._properties_by_attr[item]
                return prop.get(prop.field, self._obj)
        except KeyError:
            pass
        raise AttributeError(item)

    def _get_properties(self) -> Iterable[Property]:
        return self._properties


class Page(NotionObject):
    id: str = RootProperty("id")
    created_time: datetime = RootProperty()
    last_edited_time: datetime = RootProperty()
