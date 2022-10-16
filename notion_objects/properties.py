import uuid
from datetime import date, datetime
from functools import cached_property
from typing import Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

import dateutil.parser

from .values import DateValue, UserValue

property_types = [
    "title",
    "rich_text",
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

_T = TypeVar("_T")


class Property(Generic[_T]):
    field: str
    attr: str
    target_type: Optional[Type] = None

    def __init__(self, field: str = None, object_locator: str = "_obj"):
        self.field = field
        self.attr = field
        self.object_locator = object_locator

    def get(self, field: str, obj: dict) -> _T:
        raise NotImplementedError(
            "get operation not implemented for property '%s'" % (self.__class__.__name__)
        )

    def set(self, field: str, value: _T, obj: dict):
        raise NotImplementedError(
            "set operation not implemented for property '%s'" % (self.__class__.__name__)
        )

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

    def __set__(self, instance, value):
        try:
            # keep track of changes
            changes = instance.__changes__
            self.set(self.field, value, changes)
        except AttributeError:
            return

        # also set the underlying object
        if self.object_locator:
            instance = getattr(instance, self.object_locator)
        self.set(self.field, value, instance["properties"])

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.field == self.attr:
            return f"{self.__class__.__name__}({self.field})"
        else:
            return f"{self.__class__.__name__}({self.field} -> {self.attr})"


class ChangeTracker:
    @cached_property
    def __changes__(self) -> Dict[str, Tuple[Property, object]]:
        return {}


class RootProperty(Property[_T]):
    def get(self, field: str, obj: dict):
        value = obj[field]
        if self.target_type == datetime:
            return dateutil.parser.parse(value)
        return value


class TitlePlainText(Property[str]):
    def get(self, field: str, obj: dict) -> str:
        items = obj["properties"][field]["title"]
        if items:
            return "".join([item["plain_text"] for item in items])
        return ""


class TitleText(Property[str]):
    def get(self, field: str, obj: dict) -> str:
        items = obj["properties"][field]["title"]
        if items:
            return "".join([item["text"]["content"] for item in items])
        return ""


class Text(Property[str]):
    def get(self, field: str, obj: dict) -> str:
        items = obj["properties"][field]["rich_text"]

        if items:
            return "".join([item["plain_text"] for item in items])

        return ""


class Email(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field]["email"]

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {"email": value}


class URL(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field]["url"]

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {"url": value}


class Phone(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field]["phone_number"]

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {"phone_number": value}


class Number(Property[Optional[Union[float, int]]]):
    def get(self, field: str, obj: dict) -> Optional[Union[float, int]]:
        return obj["properties"][field]["number"]

    def set(self, field: str, value: Union[float, int], obj: dict):
        obj[field] = {"number": value}


class Integer(Property[Optional[int]]):
    def get(self, field: str, obj: dict) -> Optional[int]:
        if value := obj["properties"][field]["number"]:
            return int(value)

    def set(self, field: str, value: Optional[int], obj: dict):
        obj[field] = {"number": value}


class Checkbox(Property[bool]):
    def get(self, field: str, obj: dict) -> bool:
        return obj["properties"][field]["checkbox"] in [True, "true"]

    def set(self, field: str, value: bool, obj: dict):
        obj[field] = {"checkbox": value}


class Select(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        select = obj["properties"][field]["select"]
        if select is None:
            return None
        return select["name"]

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {"select": {"name": value} if value is not None else None}


class MultiSelect(Property[List[str]]):
    def get(self, field: str, obj: dict) -> List[str]:
        return [s["name"] for s in obj["properties"][field].get("multi_select", [])]

    def set(self, field: str, value: List[str], obj: dict):
        obj[field] = {"multi_select": [{"name": v} for v in value]}


class Status(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        if status := obj["properties"][field]["status"]:
            return status["name"]

    def set(self, field: str, value: Optional[str], obj: dict):
        status = {"name": value} if value is not None else {}
        obj[field] = {"status": status}


class DateProperty(Property[DateValue]):
    def get(self, field: str, obj: dict) -> DateValue:
        return self.get_value(field, obj)

    def set(self, field: str, value: DateValue, obj: dict):
        self.set_value(field, value, obj)

    @staticmethod
    def get_value(field: str, obj: dict) -> DateValue:
        # TODO: timezone

        start, end = None, None
        include_time = False

        if container := obj["properties"][field]["date"]:
            if date_str := container["start"]:
                start = dateutil.parser.parse(date_str)
                if len(date_str) > 10:
                    include_time = True

        if container := obj["properties"][field]["date"]:
            if date_str := container["end"]:
                end = dateutil.parser.parse(date_str)
                if len(date_str) > 10:
                    include_time = True

        if not include_time:
            if start:
                start = start.date()
            if end:
                end = end.date()

        return DateValue(start, end, include_time, None)

    @staticmethod
    def set_value(field: str, value: DateValue, obj: dict):
        if value.start is None and value.end is None:
            obj[field] = {"date": {}}

        obj[field] = {
            "date": {
                "start": value.start.isoformat() if value.start else None,
                "end": value.end.isoformat() if value.is_range else None,
                "time_zone": str(value.time_zone) if value.time_zone else None,  # TODO
            }
        }


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
            if date_str := container["start"]:
                start = dateutil.parser.parse(date_str)

        if container := obj["properties"][field]["date"]:
            if date_str := container["end"]:
                end = dateutil.parser.parse(date_str)

        return start, end


class DateRange(Property[Tuple[Optional[date], Optional[date]]]):
    def get(self, field: str, obj: dict) -> Tuple[Optional[date], Optional[date]]:
        start, end = None, None

        if container := obj["properties"][field]["date"]:
            if date_str := container["start"]:
                start = dateutil.parser.parse(date_str).date()

        if container := obj["properties"][field]["date"]:
            if date_str := container["end"]:
                end = dateutil.parser.parse(date_str).date()

        return start, end


class DateRangeStart(Property[Optional[date]]):
    def get(self, field: str, obj: dict) -> Optional[date]:
        container = obj["properties"][field]["date"]
        if container is None:
            return None
        else:
            if start := container["start"]:
                return dateutil.parser.parse(start).date()


class DateRangeEnd(Property[Optional[date]]):
    def get(self, field: str, obj: dict) -> Optional[date]:
        container = obj["properties"][field]["date"]
        if container is None:
            return None
        else:
            if end := container["end"]:
                return dateutil.parser.parse(end).date()


class PeopleProperty(Property[List[UserValue]]):
    def get(self, field: str, obj: dict) -> List[UserValue]:
        return self.get_value(field, obj)

    def set(self, field: str, value: List[UserValue], obj: dict):
        return self.set_value(field, value, obj)

    @staticmethod
    def get_value(field: str, obj: dict) -> List[UserValue]:
        return [
            UserValue(item["id"], item.get("name"))
            for item in obj["properties"][field].get("people", [])
        ]

    @staticmethod
    def set_value(field: str, value: List[Union[str, UserValue]], obj: dict):
        if not value:
            obj[field] = {"people": []}
            return

        try:
            obj[field] = {
                "people": [
                    {"object": "user", "id": str(uuid.UUID(user)) if type(user) == str else user.id}
                    for user in value
                ]
            }
        except Exception as e:
            raise ValueError("user value must be a UUID") from e


class Person(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        people = PeopleProperty.get_value(field, obj)
        if not people:
            return None

        return people[0].name or people[0].id

    def set(self, field: str, value: str, obj: dict):
        PeopleProperty.set_value(field, [value], obj)


class People(Property[List[str]]):
    def get(self, field: str, obj: dict) -> List[str]:
        people = PeopleProperty.get_value(field, obj)
        return [person.name or person.id for person in people]

    def set(self, field: str, value: List[str], obj: dict):
        PeopleProperty.set_value(field, value, obj)


class Properties:
    factories: Dict[str, Type[Property]] = {
        "title": TitleText,
        "created_time": CreatedTime,
        "select": Select,
        "rich_text": Text,
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
                if not prop["date"]:
                    # in most cases we can't make any assumptions about the date format,
                    # so we just fall back to the most general case, which is DateTimeRange.
                    result.append(DateProperty(field=field))

                # TODO: timezone
                elif "end" not in prop["date"]:
                    if start := prop["date"].get("start"):
                        if len(start) > 10:
                            result.append(DateTime(field=field))
                        else:
                            result.append(Date(field=field))
                    else:
                        result.append(Date(field=field))
                else:
                    if len(prop["date"].get("end") or "") > 10:
                        result.append(DateTimeRange(field=field))
                    else:
                        result.append(DateRange(field=field))

        return Properties(result)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Properties({self.properties})"
