import inspect
from datetime import datetime
from typing import Iterable, List

from .encode import _ConverterMixin
from .properties import ChangeTracker, Id, Properties, Property, RootProperty


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


class NotionObject(_ConverterMixin, ChangeTracker, metaclass=NotionClass):
    _obj: dict

    def __init__(self, obj):
        self._obj = obj

    def _get_properties(self) -> Iterable[Property]:
        return self.__properties__

    @classmethod
    def new(cls, **kwargs):
        """
        Creates a new unmanaged object.

        :param kwargs: the object attributes
        :return: a new object that can be added with Database.create(obj)
        """
        obj = cls({"properties": {}})

        for k, v in kwargs.items():
            setattr(obj, k, v)

        return obj


class DynamicNotionObject(_ConverterMixin, ChangeTracker):
    _properties: Properties
    _obj: dict

    def __init__(self, obj: dict, properties: Properties = None):
        super(DynamicNotionObject, self).__init__()
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

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __setitem__(self, key, value):
        try:
            if key in self._properties_by_attr:
                prop = self._properties_by_attr[key]
                prop.set(prop.field, value, self._obj["properties"])
                return prop.set(prop.field, value, self.__changes__)
        except KeyError:
            pass
        raise AttributeError(key)

    def _get_properties(self) -> Iterable[Property]:
        return self._properties

    def __str__(self):
        return f"DynamicNotionObject({str(self.to_dict())})"


class Page(NotionObject):
    id: str = Id()
    created_time: datetime = RootProperty()
    last_edited_time: datetime = RootProperty()
