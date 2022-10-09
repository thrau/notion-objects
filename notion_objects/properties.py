from datetime import date, datetime
from typing import Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

import dateutil.parser

_T = TypeVar("_T")

property_types = [
    "title",
    "rich_text",  # TODO
    "number",
    "select",
    "multi_select",
    "date",
    "people",
    "files",  # TODO
    "checkbox",
    "url",
    "email",
    "phone_number",
    "formula",  # TODO
    "relation",  # TODO
    "rollup",  # TODO
    "created_time",
    "created_by",  # TODO
    "last_edited_time",
    "last_edited_by",  # TODO
    "status",
]


class Property(Generic[_T]):
    field: str
    attr: str
    target_type: Optional[Type] = None

    def __init__(self, field: str = None, object_locator: str = "_obj"):
        self.field = field
        self.attr = field
        self.object_locator = object_locator

    def get(self, field: str, obj: dict) -> _T:
        raise NotImplementedError

    def __set_name__(self, owner, name):
        self.attr = name

        if self.field is None:
            self.field = name

        try:
            self.target_type = owner.__annotations__[self.attr]
        except KeyError:
            self.target_type = None

    def __get__(self, instance, owner):
        if self.object_locator:
            return self.get(self.field, getattr(instance, self.object_locator))
        else:
            return self.get(self.field, instance)


class RootProperty(Property[_T]):
    def get(self, field: str, obj: dict):
        value = obj[field]
        if self.target_type == datetime:
            return dateutil.parser.parse(value)
        return value


class TitlePlainText(Property[str]):
    def get(self, field: str, obj: dict) -> str:
        try:
            return obj["properties"][field]["title"][0]["plain_text"]
        except IndexError:
            return ""


class TitleText(Property[str]):
    def get(self, field: str, obj: dict) -> str:
        try:
            return obj["properties"][field]["title"][0]["text"]["content"]
        except IndexError:
            return ""


class Email(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field]["email"]


class URL(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field]["url"]


class Phone(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field]["phone_number"]


class Number(Property[Optional[Union[float, int]]]):
    def get(self, field: str, obj: dict) -> Optional[Union[float, int]]:
        return obj["properties"][field]["number"]


class Integer(Property[Optional[int]]):
    def get(self, field: str, obj: dict) -> Optional[int]:
        if value := obj["properties"][field]["number"]:
            return int(value)


class Checkbox(Property[bool]):
    def get(self, field: str, obj: dict) -> bool:
        return obj["properties"][field]["checkbox"] in [True, "true"]


class Select(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        select = obj["properties"][field]["select"]
        if select is None:
            return None
        return select["name"]


class MultiSelect(Property[List[str]]):
    def get(self, field: str, obj: dict) -> List[str]:
        return [s["name"] for s in obj["properties"][field].get("multi_select", [])]


class Status(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        if status := obj["properties"][field]["status"]:
            return status["name"]


class CreatedTime(Property[datetime]):
    def get(self, field: str, obj: dict) -> datetime:
        return dateutil.parser.parse(obj["properties"][field]["created_time"])


class Date(Property[Optional[date]]):
    def get(self, field: str, obj: dict) -> Optional[date]:
        if container := obj["properties"][field]["date"]:
            return dateutil.parser.parse(container["start"]).date()
        return None


class DateTime(Property[Optional[datetime]]):
    def get(self, field: str, obj: dict) -> Optional[datetime]:
        if container := obj["properties"][field]["date"]:
            return dateutil.parser.parse(container["start"])
        return None


class DateTimeRange(Property[Tuple[Optional[datetime], Optional[datetime]]]):
    def get(self, field: str, obj: dict) -> Tuple[Optional[datetime], Optional[datetime]]:
        start, end = None, None

        if container := obj["properties"][field]["date"]:
            start = dateutil.parser.parse(container["start"])

        if container := obj["properties"][field]["date"]:
            end = dateutil.parser.parse(container["end"])

        return start, end


class DateRange(Property[Tuple[Optional[date], Optional[date]]]):
    def get(self, field: str, obj: dict) -> Tuple[Optional[date], Optional[date]]:
        start, end = None, None

        if container := obj["properties"][field]["date"]:
            start = dateutil.parser.parse(container["start"]).date()

        if container := obj["properties"][field]["date"]:
            end = dateutil.parser.parse(container["end"]).date()

        return start, end


class DateRangeStart(Property[Optional[date]]):
    def get(self, field: str, obj: dict) -> Optional[date]:
        container = obj["properties"][field]["date"]
        if container is None:
            return None
        else:
            return dateutil.parser.parse(container["start"]).date()


class DateRangeEnd(Property[Optional[date]]):
    def get(self, field: str, obj: dict) -> Optional[date]:
        container = obj["properties"][field]["date"]
        if container is None:
            return None
        else:
            return dateutil.parser.parse(container["end"]).date()


class Person(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        try:
            return obj["properties"][field]["people"][0]["name"]
        except IndexError:
            return None
        except KeyError:
            return obj["properties"][field]["people"][0]["id"]


class People(Property[List[str]]):
    def get(self, field: str, obj: dict) -> List[str]:
        people = []

        for p in obj["properties"][field]["people"]:
            try:
                people.append(p["name"])
            except KeyError:
                people.append(p["id"])

        return people


class Properties:
    factories: Dict[str, Type[Property]] = {
        "title": TitleText,
        "created_time": CreatedTime,
        "select": Select,
        "multi_select": MultiSelect,
        "people": People,
        "phone_number": Phone,
        "status": Status,
        "url": URL,
        "email": Email,
        "checkbox": Checkbox,
        "number": Number,
        # TODO: ...
    }

    properties: List[Property]

    def __init__(self, properties: List[Property]):
        self.properties = properties

    def __iter__(self):
        return self.properties.__iter__()

    @classmethod
    def parse(cls, obj: dict) -> "Properties":
        created_time = RootProperty("created_time")
        created_time.target_type = datetime

        last_edited_time = RootProperty("last_edited_time")
        last_edited_time.target_type = datetime

        result = [
            RootProperty("id"),
            created_time,
            last_edited_time,
        ]

        for field, prop in obj["properties"].items():
            field_type = prop["type"]

            if field_type in cls.factories:
                result.append(cls.factories[field_type](field=field))

            # we have to peek into the value to get the correct type for dates
            elif field_type == "date":
                # TODO: timezone
                if "end" not in prop["date"]:
                    if start := prop["date"].get("start"):
                        if len(start) > 10:
                            result.append(DateTime(field=field))
                        else:
                            result.append(Date(field=field))
                    else:
                        result.append(Date(field=field))
                else:
                    if len(prop["date"].get("end")) > 10:
                        result.append(DateTimeRange(field=field))
                    else:
                        result.append(DateRange(field=field))

        return Properties(result)
