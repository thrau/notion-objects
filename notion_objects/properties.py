import uuid
from datetime import date, datetime
from functools import cached_property
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import dateutil.parser

from . import rich_text
from .values import DateValue, UniqueIdValue, UserValue

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
    "relation",
    "rollup",  # TODO
    "created_time",
    "created_by",  # TODO
    "last_edited_time",
    "last_edited_by",  # TODO
    "status",
    "emoji",  # TODO
    "external",  # TODO
    "unique_id",
]

PropertyType = Literal[
    "checkbox",
    "created_by",
    "created_time",
    "date",
    "email",
    "files",
    "formula",
    "last_edited_by",
    "last_edited_time",
    "multi_select",
    "number",
    "people",
    "phone_number",
    "relation",
    "rich_text",
    "rollup",
    "select",
    "status",
    "title",
    "unique_id",
    "url",
]
"""The notion data type of a property, see https://developers.notion.com/reference/property-object."""

_T = TypeVar("_T")
_P = TypeVar("_P", bound="Property")


class Property(Generic[_T]):
    """
    A descriptor for mappings between a notion database property and a python attribute.

    """

    field: str
    """The name of the property in the notion database."""
    attr: str
    """The name of the attribute in the mapped python object."""
    type: Optional[PropertyType] = None
    """The notion data type of a property."""
    target_type: Optional[Type] = None
    """The python type this property should be mapped to."""

    def __init__(self, field: str = None, object_locator: str = "_obj"):
        self.field = field
        self.attr = field
        self.object_locator = object_locator

    def get(self, field: str, obj: dict) -> _T:
        """
        Extract from the given field in a notion object the corresponding python value.

        :param field: the notion database property name
        :param obj: the notion database object
        :return: a python value representing the value in the notion property
        """
        raise NotImplementedError(
            f"get operation not implemented for property '{self.__class__.__name__}'"
        )

    def set(self, field: str, value: _T, obj: dict):
        """
        Maps a given python attribute value to the corresponding notion object property.

        :param field: the notion database property name
        :param value: the python value to set
        :param obj: the notion database object
        """
        raise NotImplementedError(
            f"set operation not implemented for property '{self.__class__.__name__}'"
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
        if instance is None:
            # instance will be None when accessing the property through class access, for instance ``Page.id``. Here we
            # return the Property instance itself, rather than the value. This helps with various meta operations.
            return self

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
    id: str

    @cached_property
    def __changes__(self) -> Dict[str, Any]:
        return {}


class RootProperty(Property[_T]):
    def get(self, field: str, obj: dict):
        value = obj[field]
        if self.target_type == datetime:
            return dateutil.parser.parse(value)
        return value


class Id(RootProperty[str]):
    def __init__(self):
        super().__init__("id")

    def __set__(self, instance, value):
        if self.object_locator:
            instance = getattr(instance, self.object_locator)
        instance[self.field] = value


class TitlePlainText(Property[str]):
    type = "title"

    def get(self, field: str, obj: dict) -> str:
        items = obj["properties"][field][self.type]
        if items:
            return "".join([item["plain_text"] for item in items])
        return ""

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {
            self.type: [
                {
                    "type": "text",
                    "text": {"content": value},
                    "plain_text": value,
                }
            ]
        }


class TitleText(Property[str]):
    type = "title"

    def get(self, field: str, obj: dict) -> str:
        items = obj["properties"][field]["title"]
        if items:
            return "".join([item["text"]["content"] for item in items])
        return ""

    def set(self, field: str, value: Optional[str], obj: dict):
        # TODO: allow rich-text
        obj[field] = {
            "title": [
                {
                    "type": "text",
                    "text": {"content": value},
                    "plain_text": value,
                }
            ]
        }


class Relation(Property[List[str]]):
    type = "relation"

    def get(self, field: str, obj: dict) -> List[str]:
        items = obj["properties"][field][self.type]
        return [item["id"] for item in items]

    def set(self, field: str, value: Union[str, Iterable[str]], obj: dict):
        if isinstance(value, str):
            ids = [value]
        else:
            ids = value

        value = obj.setdefault(field, {})
        value[self.type] = [{"id": id_} for id_ in ids]


class Text(Property[str]):
    type = "rich_text"

    def get(self, field: str, obj: dict) -> str:
        items = obj["properties"][field]["rich_text"]

        if items:
            return "".join([item["plain_text"] for item in items])

        return ""

    def set(self, field: str, value: Optional[Union[str, rich_text.RichTextObject]], obj: dict):
        if value is None:
            obj[field] = {"rich_text": []}
            return

        if not isinstance(value, rich_text.RichTextObject):
            value = rich_text.RichText(value)

        # TODO: allow rich-text
        obj[field] = {"rich_text": [value.to_dict()]}


class RichTextProperty(Property[List[rich_text.RichTextObject]]):
    type = "rich_text"

    def get(self, field: str, obj: dict) -> List[rich_text.RichTextObject]:
        items = obj["properties"][field][self.type]
        if items:
            return [rich_text.parse(item) for item in items]
        return []

    def set(
        self,
        field: str,
        value: Optional[Union[List[rich_text.RichTextObject], rich_text.RichTextObject]],
        obj: dict,
    ):
        if not value:
            obj[field] = {self.type: []}
            return
        if isinstance(value, str):
            value = [rich_text.RichText(value)]
        elif isinstance(value, rich_text.RichTextObject):
            value = [value]

        obj[field] = {"rich_text": [rt.to_dict() for rt in value]}


class _SimpleStringProperty(Property[Optional[str]]):
    def get(self, field: str, obj: dict) -> Optional[str]:
        return obj["properties"][field][self.type]

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {self.type: value}


class Email(_SimpleStringProperty):
    type = "email"


class URL(_SimpleStringProperty):
    type = "url"


class Phone(_SimpleStringProperty):
    type = "phone_number"


class Number(Property[Optional[Union[float, int]]]):
    type = "number"

    def get(self, field: str, obj: dict) -> Optional[Union[float, int]]:
        return obj["properties"][field][self.type]

    def set(self, field: str, value: Optional[Union[float, int, str]], obj: dict):
        if isinstance(value, str):
            if "." in value:
                value = float(value)
            else:
                value = int(value)
        obj[field] = {self.type: value}


class UniqueId(Property[UniqueIdValue]):
    type = "unique_id"

    def get(self, field: str, obj: dict) -> UniqueIdValue:
        return UniqueIdValue(**obj["properties"][field][self.type])

    def set(self, field: str, value: _T, obj: dict):
        raise NotImplementedError("setting unique IDs is not possible yet")


class Integer(Property[Optional[int]]):
    type = "number"

    def get(self, field: str, obj: dict) -> Optional[int]:
        if value := obj["properties"][field][self.type]:
            return int(value)

    def set(self, field: str, value: Optional[Union[int, str]], obj: dict):
        if isinstance(value, str):
            value = int(value)
        obj[field] = {self.type: value}


class Checkbox(Property[bool]):
    type = "checkbox"

    def get(self, field: str, obj: dict) -> bool:
        return obj["properties"][field][self.type] in [True, "true"]

    def set(self, field: str, value: Optional[bool], obj: dict):
        obj[field] = {self.type: value}


class Select(Property[Optional[str]]):
    type = "select"

    def get(self, field: str, obj: dict) -> Optional[str]:
        select = obj["properties"][field][self.type]
        if select is None:
            return None
        return select["name"]

    def set(self, field: str, value: Optional[str], obj: dict):
        obj[field] = {self.type: {"name": value} if value is not None else None}


class MultiSelect(Property[List[str]]):
    type = "multi_select"

    def get(self, field: str, obj: dict) -> List[str]:
        return [s["name"] for s in obj["properties"][field].get(self.type, [])]

    def set(self, field: str, value: Optional[List[str]], obj: dict):
        obj[field] = {self.type: [{"name": v} for v in value] if value is not None else None}


class Status(Property[Optional[str]]):
    type = "status"

    def get(self, field: str, obj: dict) -> Optional[str]:
        if status := obj["properties"][field][self.type]:
            return status["name"]

    def set(self, field: str, value: Optional[str], obj: dict):
        status = {"name": value} if value is not None else {}
        obj[field] = {self.type: status}


class DateProperty(Property[DateValue]):
    type = "date"

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
            obj[field] = {"date": None}
            return

        obj[field] = {
            "date": {
                "start": value.start.isoformat() if value.start else None,
                "end": value.end.isoformat() if value.is_range else None,
                "time_zone": str(value.time_zone) if value.time_zone else None,  # TODO
            }
        }


class CreatedTime(Property[datetime]):
    type = "created_time"

    def get(self, field: str, obj: dict) -> datetime:
        return dateutil.parser.parse(obj["properties"][field][self.type])


_DatePrimitive = Union[str, date, datetime]

_DateVariety = Optional[
    Union[DateValue, _DatePrimitive, Tuple[Optional[_DatePrimitive], Optional[_DatePrimitive]]]
]


class _DateSetMixin:
    include_time: bool

    def set_date_value(self, field: str, value: _DateVariety, obj: dict):
        if isinstance(value, DateValue):
            return DateProperty.set_value(field, value, obj)

        if isinstance(value, tuple):
            start, end = value
        else:
            start, end = value, None

        if isinstance(start, str):
            start = dateutil.parser.parse(start)
        if isinstance(end, str):
            end = dateutil.parser.parse(end)

        if isinstance(start, datetime) and not self.include_time:
            start = start.date()
        if isinstance(end, datetime) and not self.include_time:
            end = end.date()

        return DateProperty.set_value(field, DateValue(start, end, self.include_time), obj)


class Date(Property[Optional[date]], _DateSetMixin):
    type = "date"
    include_time = False

    def get(self, field: str, obj: dict) -> Optional[date]:
        if container := obj["properties"][field][self.type]:
            return dateutil.parser.parse(container["start"]).date()
        return None

    def set(self, field: str, value: Optional[Union[date, str]], obj: dict):
        self.set_date_value(field, value, obj)


class DateTime(Property[Optional[datetime]], _DateSetMixin):
    type = "date"
    include_time = True

    def get(self, field: str, obj: dict) -> Optional[datetime]:
        if container := obj["properties"][field]["date"]:
            return dateutil.parser.parse(container["start"])
        return None

    def set(self, field: str, value: Optional[Union[datetime, str]], obj: dict):
        self.set_date_value(field, value, obj)


class DateTimeRange(Property[Tuple[Optional[datetime], Optional[datetime]]], _DateSetMixin):
    type = "date"

    include_time = True

    def get(self, field: str, obj: dict) -> Tuple[Optional[datetime], Optional[datetime]]:
        start, end = None, None

        if container := obj["properties"][field]["date"]:
            if date_str := container["start"]:
                start = dateutil.parser.parse(date_str)

        if container := obj["properties"][field]["date"]:
            if date_str := container["end"]:
                end = dateutil.parser.parse(date_str)

        return start, end

    def set(
        self,
        field: str,
        value: Optional[Tuple[Optional[Union[datetime, str]], Optional[Union[datetime, str]]]],
        obj: dict,
    ):
        self.set_date_value(field, value, obj)


class DateRange(Property[Tuple[Optional[date], Optional[date]]], _DateSetMixin):
    type = "date"
    include_time = False

    def get(self, field: str, obj: dict) -> Tuple[Optional[date], Optional[date]]:
        start, end = None, None

        if container := obj["properties"][field]["date"]:
            if date_str := container["start"]:
                start = dateutil.parser.parse(date_str).date()

        if container := obj["properties"][field]["date"]:
            if date_str := container["end"]:
                end = dateutil.parser.parse(date_str).date()

        return start, end

    def set(
        self,
        field: str,
        value: Optional[Tuple[Optional[Union[date, str]], Optional[Union[date, str]]]],
        obj: dict,
    ):
        self.set_date_value(field, value, obj)


class DateRangeStart(Property[Optional[date]]):
    type = "date"

    def get(self, field: str, obj: dict) -> Optional[date]:
        container = obj["properties"][field]["date"]
        if container is None:
            return None
        else:
            if start := container["start"]:
                return dateutil.parser.parse(start).date()


class DateRangeEnd(Property[Optional[date]]):
    type = "date"

    def get(self, field: str, obj: dict) -> Optional[date]:
        container = obj["properties"][field]["date"]
        if container is None:
            return None
        else:
            if end := container["end"]:
                return dateutil.parser.parse(end).date()


class PeopleProperty(Property[List[UserValue]]):
    type = "people"

    def get(self, field: str, obj: dict) -> List[UserValue]:
        return self.get_value(field, obj)

    def set(self, field: str, value: List[UserValue], obj: dict):
        return self.set_value(field, value, obj)

    @staticmethod
    def get_value(field: str, obj: dict) -> List[UserValue]:
        return [
            UserValue(item["id"], item.get("name"), item.get("person", {}).get("email"))
            for item in obj["properties"][field].get("people", [])
        ]

    @staticmethod
    def set_value(field: str, value: Optional[List[Union[str, UserValue]]], obj: dict):
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
    type = "people"

    def get(self, field: str, obj: dict) -> Optional[str]:
        people = PeopleProperty.get_value(field, obj)
        if not people:
            return None

        return people[0].name or people[0].id

    def set(self, field: str, value: Optional[str], obj: dict):
        PeopleProperty.set_value(field, [value] if value is not None else None, obj)


class People(Property[List[str]]):
    type = "people"

    def get(self, field: str, obj: dict) -> List[str]:
        people = PeopleProperty.get_value(field, obj)
        return [person.name or person.id for person in people]

    def set(self, field: str, value: List[str], obj: dict):
        PeopleProperty.set_value(field, value, obj)


class Properties(Iterable[_P]):
    factories: Dict[PropertyType, Type[Property]] = {
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
        "relation": Relation,
        # TODO: ...
    }

    properties: List[_P]

    def __init__(self, properties: List[_P]):
        self.properties = properties

    def __iter__(self):
        return self.properties.__iter__()

    def __getitem__(self, item) -> _P:
        for prop in self.properties:
            if prop.field == item:
                return prop
        raise KeyError(f"No such property field {item}")

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
