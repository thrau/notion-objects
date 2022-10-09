from collections import defaultdict
from datetime import date, datetime
from typing import Generic, List, Optional, Type, TypeVar

import dateutil.parser

_T = TypeVar("_T")


class Attribute(Generic[_T]):
    field: str
    attr: str
    target_type: Optional[Type]

    def __init__(self, field: str = None, object_locator: str = "_obj"):
        self.field = field
        self.object_locator = object_locator

    def get(self, obj) -> _T:
        raise NotImplementedError

    def __set_name__(self, owner, name):
        self.attr = name

        if self.field is None:
            self.field = name

        try:
            attrs = getattr(owner, "_notion_attrs_")
        except AttributeError:
            owner._notion_attrs_ = defaultdict(list)
            attrs = owner._notion_attrs_

        attrs[owner].append(self)

        try:
            self.target_type = owner.__annotations__[self.attr]
        except KeyError:
            self.target_type = None

    def __get__(self, instance, owner):
        if self.object_locator:
            return self.get(getattr(instance, self.object_locator))
        else:
            return self.get(instance)


class RootAttribute(Attribute[_T]):
    def get(self, obj):
        value = obj[self.field]
        if self.target_type == datetime:
            return dateutil.parser.parse(value)
        return value


class Title(Attribute[str]):
    def get(self, obj) -> str:
        try:
            return obj["properties"][self.field]["title"][0]["plain_text"]
        except IndexError:
            return ""


class Select(Attribute[Optional[str]]):
    def get(self, obj) -> Optional[str]:
        select = obj["properties"][self.field]["select"]
        if select is None:
            return None
        return select["name"]


class Status(Attribute[Optional[str]]):
    def get(self, obj) -> Optional[str]:
        if status := obj["properties"][self.field]["status"]:
            return status["name"]


class Phone(Attribute[Optional[str]]):
    def get(self, obj) -> Optional[str]:
        return obj["properties"][self.field]["phone_number"]


class DateRangeStart(Attribute[Optional[date]]):
    def get(self, obj) -> Optional[date]:
        container = obj["properties"][self.field]["date"]
        if container is None:
            return None
        else:
            return dateutil.parser.parse(container["start"]).date()


class DateRangeEnd(Attribute[Optional[date]]):
    def get(self, obj) -> Optional[date]:
        container = obj["properties"][self.field]["date"]
        if container is None:
            return None
        else:
            return dateutil.parser.parse(container["end"]).date()


class Person(Attribute[Optional[str]]):
    def get(self, obj) -> Optional[str]:
        try:
            return obj["properties"][self.field]["people"][0]["name"]
        except IndexError:
            return None
        except KeyError:
            return obj["properties"][self.field]["people"][0]["id"]


class People(Attribute[List[str]]):
    def get(self, obj) -> List[str]:
        people = []

        for p in obj["properties"][self.field]["people"]:
            try:
                people.append(p["name"])
            except KeyError:
                people.append(p["id"])

        return people
