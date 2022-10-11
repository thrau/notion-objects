import json
from datetime import date, datetime
from unittest.mock import MagicMock

from dateutil.tz import tzutc

from notion_objects import (
    DateRangeEnd,
    DateRangeStart,
    MultiSelect,
    Page,
    Person,
    Phone,
    Select,
    Status,
    TitlePlainText,
)
from notion_objects.database import Database


class SampleObject(Page):
    name = TitlePlainText("Name")
    status = Status("Status")
    person = Person("Person")
    my_select = Select("My select")
    date_start = DateRangeStart("Date")
    date_end = DateRangeEnd("Date")
    Phone = Phone()
    Tags = MultiSelect()


def test_database_iterable():
    # terrible greybox test

    class _FakeDatabase:
        responses = [
            '{"object": "list", "results": [{"object": "page", "id": "794e8d6f-e25a-4071-a630-ec1f24eee771", "created_time": "2022-10-11T15:44:00.000Z", "last_edited_time": "2022-10-11T15:45:00.000Z", "created_by": {"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328"}, "last_edited_by": {"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328"}, "cover": null, "icon": null, "parent": {"type": "database_id", "database_id": "cc49be95-3623-498f-9015-d462a7cdb91f"}, "archived": false, "properties": {"My select": {"id": "Hs%5Dj", "type": "select", "select": null}, "Created time": {"id": "Jv%60q", "type": "created_time", "created_time": "2022-10-11T15:44:00.000Z"}, "Person": {"id": "WC%5CO", "type": "people", "people": [{"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328", "name": "Thomas", "avatar_url": "https://s3-us-west-2.amazonaws.com/public.notion-static.com/6de82026-ba35-4817-8626-a5546031db4e/portrait-square.jpg", "type": "person", "person": {"email": "thomas@localstack.cloud"}}]}, "Status": {"id": "%5DvNj", "type": "status", "status": null}, "Date": {"id": "_PPi", "type": "date", "date": {"start": "2022-10-11", "end": null, "time_zone": null}}, "Tags": {"id": "sAAp", "type": "multi_select", "multi_select": [{"id": "3518feab-87c2-4641-a8af-20b4947003d4", "name": "hello", "color": "gray"}]}, "Phone": {"id": "zd%3AH", "type": "phone_number", "phone_number": null}, "Name": {"id": "title", "type": "title", "title": [{"type": "text", "text": {"content": "another page", "link": null}, "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}, "plain_text": "another page", "href": null}]}}, "url": "https://www.notion.so/another-page-62e9f991d42d41869e79546c87be7d06"}, {"object": "page", "id": "390100a5-4808-4236-b8b4-87352b65c403", "created_time": "2022-10-08T22:29:00.000Z", "last_edited_time": "2022-10-09T00:48:00.000Z", "created_by": {"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328"}, "last_edited_by": {"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328"}, "cover": null, "icon": null, "parent": {"type": "database_id", "database_id": "cc49be95-3623-498f-9015-d462a7cdb91f"}, "archived": false, "properties": {"My select": {"id": "Hs%5Dj", "type": "select", "select": {"id": "ffc9b948-864c-4044-aff2-27fed1df1427", "name": "b", "color": "purple"}}, "Created time": {"id": "Jv%60q", "type": "created_time", "created_time": "2022-10-08T22:29:00.000Z"}, "Person": {"id": "WC%5CO", "type": "people", "people": []}, "Status": {"id": "%5DvNj", "type": "status", "status": null}, "Date": {"id": "_PPi", "type": "date", "date": null}, "Tags": {"id": "sAAp", "type": "multi_select", "multi_select": []}, "Phone": {"id": "zd%3AH", "type": "phone_number", "phone_number": "+10900234123"}, "Name": {"id": "title", "type": "title", "title": [{"type": "text", "text": {"content": "a second page", "link": null}, "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}, "plain_text": "a second page", "href": null}]}}, "url": "https://www.notion.so/a-second-page-390234a54918423c68b4d7359ba5c403"}], "next_cursor": "db14e46a-c365-454e-9408-7b1841b593e4", "has_more": true, "type": "page", "page": {}}',
            '{"object": "list", "results": [{"object": "page", "id": "ea329848-0c05-48ee-950a-8df7578a5bd0", "created_time": "2022-10-08T22:29:00.000Z", "last_edited_time": "2022-10-09T00:48:00.000Z", "created_by": {"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328"}, "last_edited_by": {"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328"}, "cover": null, "icon": null, "parent": {"type": "database_id", "database_id": "cc49be95-3623-498f-9015-d462a7cdb91f"}, "archived": false, "properties": {"My select": {"id": "Hs%5Dj", "type": "select", "select": {"id": "90d37b63-e696-49f7-a361-73de72250ced", "name": "a", "color": "yellow"}}, "Created time": {"id": "Jv%60q", "type": "created_time", "created_time": "2022-10-08T22:29:00.000Z"}, "Person": {"id": "WC%5CO", "type": "people", "people": [{"object": "user", "id": "3fd2f9aa-a320-4e7d-83a2-f489299a3328", "name": "Thomas", "avatar_url": "https://s3-us-west-2.amazonaws.com/public.notion-static.com/6de82026-ba35-4817-8626-a5546031db4e/portrait-square.jpg", "type": "person", "person": {"email": "thomas@localstack.cloud"}}]}, "Status": {"id": "%5DvNj", "type": "status", "status": {"id": "8a9dd46d-625f-470e-91ef-dd16a1e9dfa4", "name": "In progress", "color": "blue"}}, "Date": {"id": "_PPi", "type": "date", "date": {"start": "2022-10-09", "end": "2022-10-09", "time_zone": null}}, "Tags": {"id": "sAAp", "type": "multi_select", "multi_select": [{"id": "a292acc3-f4f2-4ead-ba9f-6b83e4c26ed1", "name": "foobar", "color": "purple"}, {"id": "859ece03-2b87-4522-a152-9d147482eebe", "name": "baz", "color": "green"}]}, "Phone": {"id": "zd%3AH", "type": "phone_number", "phone_number": "+4369912345678"}, "Name": {"id": "title", "type": "title", "title": [{"type": "text", "text": {"content": "A page", "link": null}, "annotations": {"bold": false, "italic": false, "strikethrough": false, "underline": false, "code": false, "color": "default"}, "plain_text": "A page", "href": null}]}}, "url": "https://www.notion.so/A-page-5dcbaef398684dd988bf5c8712f8b4ab"}], "next_cursor": null, "has_more": false, "type": "page", "page": {}}',
        ]

        def __init__(self):
            self.index = 0
            self.next_token = None

        def query(self, database_id, **kwargs):
            assert self.index <= 1  # assert max two calls
            # assert database ID is always correct
            assert database_id == "cc49be95-3623-498f-9015-d462a7cdb91f"

            if self.index == 1:
                # check that in the second call, the next cursor is passed
                assert kwargs["start_cursor"] == "db14e46a-c365-454e-9408-7b1841b593e4"

            response = self.responses[self.index]
            self.index += 1
            return json.loads(response)

    client = MagicMock()
    client.databases = _FakeDatabase()

    db = Database(SampleObject, database_id="cc49be95-3623-498f-9015-d462a7cdb91f", client=client)

    records = list(db.query({"page_size": 2}))

    assert records[0].to_dict() == {
        "id": "794e8d6f-e25a-4071-a630-ec1f24eee771",
        "created_time": datetime(2022, 10, 11, 15, 44, tzinfo=tzutc()),
        "last_edited_time": datetime(2022, 10, 11, 15, 45, tzinfo=tzutc()),
        "Phone": None,
        "Tags": ["hello"],
        "date_end": None,
        "date_start": date(2022, 10, 11),
        "my_select": None,
        "name": "another page",
        "person": "Thomas",
        "status": None,
    }

    assert records[1].to_dict() == {
        "id": "390100a5-4808-4236-b8b4-87352b65c403",
        "created_time": datetime(2022, 10, 8, 22, 29, tzinfo=tzutc()),
        "last_edited_time": datetime(2022, 10, 9, 0, 48, tzinfo=tzutc()),
        "Phone": "+10900234123",
        "Tags": [],
        "date_end": None,
        "date_start": None,
        "my_select": "b",
        "name": "a second page",
        "person": None,
        "status": None,
    }

    assert records[2].to_dict() == {
        "id": "ea329848-0c05-48ee-950a-8df7578a5bd0",
        "created_time": datetime(2022, 10, 8, 22, 29, tzinfo=tzutc()),
        "last_edited_time": datetime(2022, 10, 9, 0, 48, tzinfo=tzutc()),
        "Phone": "+4369912345678",
        "Tags": ["foobar", "baz"],
        "date_end": date(2022, 10, 9),
        "date_start": date(2022, 10, 9),
        "my_select": "a",
        "name": "A page",
        "person": "Thomas",
        "status": "In progress",
    }

    assert client.databases.index == 2, "expected two calls to databases.query"
