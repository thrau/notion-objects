import copy
import uuid
from functools import cached_property, lru_cache
from typing import Any, Callable, Generic, Iterable, List, Optional, Type, TypeVar, Union, overload

from notion_client import APIResponseError, Client

from .objects import DynamicNotionObject, NotionObject
from .properties import ChangeTracker, Properties, Property

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

    @overload
    def __init__(
        self,
        database_id: str,
        client: Client,
        mapped_type: Union[
            Type[_N], Type[DynamicNotionObject], Callable[[DatabaseRecord], _N]
        ] = None,
    ):
        ...

    @overload
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
        self.type = mapped_type or self._from_database_properties

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

    @cached_property
    def title(self) -> str:
        """
        Returns the plain text name of the database.
        """
        return "".join([text["plain_text"] for text in self._database_object()["title"]])

    def _from_database_properties(self, obj: dict) -> DynamicNotionObject:
        return DynamicNotionObject(obj, self.properties)

    @property
    def id(self) -> str:
        return self._database_object()["id"]

    @property
    def url(self) -> str:
        return self._database_object()["url"]

    @lru_cache()
    def _database_object(self):
        return self.client.databases.retrieve(self.database_id)

    def find_by_id(self, page_id: str) -> Optional[_N]:
        try:
            page = self.client.pages.retrieve(page_id)
        except APIResponseError as e:
            if e.status == 404:
                return None
            raise

        if uuid.UUID(page["parent"]["database_id"]) != uuid.UUID(self.database_id):
            # page exists but does not belong to this database
            return None

        return self.type(page)

    def find_unique_by_value(self, property: Property, value: Any) -> Optional[_N]:
        """
        Runs ``query_by_value`` and then returns the first element found, or None if the result was epmty.

        :param property: property to look up
        :param value: the value to match
        :return: optional result
        """
        for item in self.query_by_value(property, value):
            return item
        return None

    def update(self, page: ChangeTracker):
        try:
            page_id = page.id
        except AttributeError:
            raise ValueError("page object needs to have an attribute 'id'")

        if not page.__changes__:
            return

        self.client.pages.update(page_id, properties=page.__changes__)

    def create(self, page: _N) -> _N:
        """
        Creates the given page in the database. The page should be created as follows::

            obj = MyPageObject.new()
            obj.my_attr = "Some Value"

            db_obj = database.create(obj)

        :param page: the page object
        :return: a new instance of the object managed in the database
        """
        return self.type(
            self.client.pages.create(
                parent={
                    "database_id": self.database_id,
                },
                properties=page._obj["properties"],
            )
        )

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

    def query_by_value(self, property: Property, value: Any) -> Iterable[_N]:
        """
        Builds an equals filter for the given property and value, and returns an iterable of items that match the value.
        Use the following pattern::

            backlog = Database(BacklogItem, ...)

            for ticket in backlog.query_by_value(BacklogItem.status, "In progress"):
                ...

        :param property: the property to search for
        :param value: the value
        :return: a list of items, can be empty
        """
        return self.query(
            {
                "filter": {
                    "property": property.field,
                    property.type: {
                        "equals": value,
                    },
                },
            }
        )
