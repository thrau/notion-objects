import copy
from typing import Callable, Generic, Iterable, Type, TypeVar, Union

from notion_client import Client

from notion_objects.objects import NotionObject

_N = TypeVar("_N", bound=NotionObject)

DatabaseRecord = dict
Query = dict


class IterableQueryExecutor(Iterable[DatabaseRecord]):
    client: Client
    query: Query

    def __init__(self, client: Client, query: Query):
        self.client = client
        self.query = query

    def execute(self) -> Iterable[DatabaseRecord]:
        query = self.query

        while True:
            result = self.client.databases.query(**query)

            for item in result["results"]:
                yield item

            if not result["has_more"]:
                return

            query["start_cursor"] = result["next_cursor"]

    def __iter__(self):
        return self.execute()


class Database(Generic[_N], Iterable[_N]):
    def __init__(
        self,
        mapped_type: Union[Type[_N], Callable[[DatabaseRecord], _N]],
        database_id: str,
        client: Client,
    ):
        self.type = mapped_type
        self.client = client
        self.database_id = database_id

    def __iter__(self):
        return self.query(query={"page_size": 100})

    def query(self, query: Query = None) -> Iterable[_N]:
        factory = self.type

        if query is None:
            query = {}
        else:
            query = copy.deepcopy(query)

        if "database_id" in query:
            if query["database_id"] != self.database_id:
                raise ValueError("database id in query does not match that of this database")
        else:
            query["database_id"] = self.database_id

        for item in IterableQueryExecutor(self.client, query=query):
            yield factory(item)
