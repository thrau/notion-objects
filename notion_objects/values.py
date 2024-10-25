from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from typing import Optional, Union

import dateutil


@dataclass
class DateValue:
    start: Optional[Union[datetime, date]]
    end: Optional[Union[datetime, date]] = None
    include_time: Optional[bool] = False
    time_zone: Optional[tzinfo] = None

    @property
    def is_range(self) -> bool:
        return self.end is not None

    @classmethod
    def from_dict(cls, date_obj: dict) -> "DateValue":
        # TODO: timezone

        start, end = None, None
        include_time = False

        if date_obj:
            if date_str := date_obj.get("start"):
                start = dateutil.parser.parse(date_str)
                if len(date_str) > 10:
                    include_time = True
                    start = start.date()

            if date_str := date_obj.get("end"):
                end = dateutil.parser.parse(date_str)
                if len(date_str) > 10:
                    include_time = True
                    end = end.date()

        return cls(start, end, include_time, None)


@dataclass
class UserValue:
    id: str
    name: Optional[str] = None
    email: Optional[str] = None

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            return self.id


@dataclass
class UniqueIdValue:
    prefix: str
    number: int

    def __str__(self):
        return f"{self.prefix}-{self.number}"
