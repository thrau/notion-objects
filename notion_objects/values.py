from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from typing import Optional, Union


@dataclass
class DateValue:
    start: Optional[Union[datetime, date]]
    end: Optional[Union[datetime, date]] = None
    include_time: Optional[bool] = False
    time_zone: Optional[tzinfo] = None

    @property
    def is_range(self) -> bool:
        return self.end is not None


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
