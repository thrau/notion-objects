import copy
import typing
from functools import cached_property, lru_cache
from typing import Callable, Generic, Iterable, Type, TypeVar, Union

from notion_client import Client

from .objects import DynamicNotionObject, NotionObject
from .properties import Properties

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
    default_page_size: int = 100

    @typing.overload
    def __init__(
        self,
        database_id: str,
        client: Client,
        mapped_type: Union[
            Type[_N], Type[DynamicNotionObject], Callable[[DatabaseRecord], _N]
        ] = None,
    ):
        ...

    @typing.overload
    def __init__(
        self,
        mapped_type: Union[Type[_N], Type[DynamicNotionObject], Callable[[DatabaseRecord], _N]],
        database_id: str,
        client: Client,
    ):
        ...

    def __init__(self, *args, **kwargs):
        if len(args) > 0 and type(args[0]) == str:
            kwargs["database_id"] = args[0]
            if len(args) > 1:
                kwargs["client"] = args[1]
            if len(args) > 2:
                kwargs["mapped_type"] = args[2]
            self._construct(**kwargs)
        else:
            self._construct(*args, **kwargs)

    def _construct(
        self,
        mapped_type: Union[
            Type[_N], Type[DynamicNotionObject], Callable[[DatabaseRecord], _N]
        ] = None,
        database_id: str = None,
        client: Client = None,
    ):
        self.database_id = database_id
        self.client = client
        self.type = mapped_type or DynamicNotionObject

    def __iter__(self):
        return self.query(query={"page_size": self.default_page_size})

    @cached_property
    def properties(self) -> Properties:
        """
        Returns the properties of the underlying database, regardless of the mapped type. Note that not all
        properties are mapped by notion-objects.

        :return: a Properties object representing the database properties.
        """
        return Properties.parse(self._database_object())

    def _from_database_properties(self, obj: dict) -> DynamicNotionObject:
        return DynamicNotionObject(obj, self.properties)

    @lru_cache()
    def _database_object(self):
        return self.client.databases.retrieve(self.database_id)

    def query(self, query: Query = None) -> Iterable[_N]:
        """
        Query the database with the given query object (see
        https://developers.notion.com/reference/post-database-query). The pagination is automatically resolved,
        so you can iterate over the entire result.

        :param query: the query
        :return: an iterable where each record is one of the mapped type notion object
        """
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
