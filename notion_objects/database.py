from typing import Callable, Generator, Generic, Iterable, TypeVar

from notion_client import Client

from notion_objects import DynamicNotionObject, NotionObject

_N = TypeVar("_N", bound=NotionObject)


class Database(Generic[_N], Iterable[_N]):
    def __init__(
        self, database_id: str, client: Client, type: Callable[[dict], _N] = DynamicNotionObject
    ):
        self.type = type
        self.client = client
        self.database_id = database_id

    def __iter__(self):
        return self.iterator(query={"page_size": 100})

    def iterator(self, query) -> Generator[_N, None, None]:
        factory = self.type
        while True:
            result = self.client.databases.query(database_id=self.database_id, **query)

            for item in result["results"]:
                yield factory(item)

            if not result["has_more"]:
                return

            query["start_cursor"] = result["next_cursor"]
