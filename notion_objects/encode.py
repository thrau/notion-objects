import dataclasses
import json
from datetime import date, datetime
from typing import Iterable

from .properties import DateRange, DateTimeRange, Property, RichTextProperty
from .values import DateValue, UniqueIdValue, UserValue


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, date):
            return o.isoformat()

        return super(JSONEncoder, self).default(o)


class _ConverterMixin:
    def to_dict(self, flat: bool = False) -> dict:
        result = {}

        for prop in self._get_properties():
            try:
                value = getattr(self, prop.attr)
            except KeyError:
                # TODO: handle more gracefully
                continue
            key = prop.attr

            if isinstance(value, UniqueIdValue):
                result[key] = str(value)
            elif isinstance(value, DateValue):
                # TODO: timezone
                if flat:
                    result[f"{key}_start"] = value.start
                    result[f"{key}_end"] = value.end
                else:
                    result[key] = {"start": value.start, "end": value.end}
            elif isinstance(value, UserValue):
                if flat:
                    result[f"{key}_id"] = value.id
                    result[f"{key}_name"] = value.name
                else:
                    result[key] = dataclasses.asdict(value)
            elif isinstance(prop, (DateRange, DateTimeRange)):
                if flat:
                    result[f"{key}_start"] = value[0]
                    result[f"{key}_end"] = value[1]
                else:
                    result[key] = {"start": value[0], "end": value[1]}
            elif isinstance(prop, RichTextProperty):
                result[key] = "".join([text.plain_text for text in value])
            else:
                result[key] = value

        return result

    def to_json(self, flat: bool = False, **kwargs):
        return json.dumps(self.to_dict(flat=flat), cls=JSONEncoder, **kwargs)

    def _get_properties(self) -> Iterable[Property]:
        raise NotImplementedError
