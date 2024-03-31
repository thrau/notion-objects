import uuid

import pytest

from notion_objects import Database, Integer, MultiSelect, Number, Page, Text, TitleText


class TestRecord(Page):
    name = TitleText()
    some_id = Integer()
    some_num = Number()
    text = Text()
    tags = MultiSelect()


class TestDatabaseQueries:
    @pytest.fixture(scope="class")
    def test_records(self):
        return [
            TestRecord.new(
                name="record 1", some_id=1, some_num=42, text="foo", tags=["tag_1", "tag_2"]
            ),
            TestRecord.new(
                name="record 2", some_id=2, some_num=42, text="bar", tags=["tag_2", "tag_3"]
            ),
            TestRecord.new(
                name="record 3", some_id=3, some_num=11, text="foo", tags=["tag_1", "tag_3"]
            ),
        ]

    @pytest.fixture(scope="class")
    def database(self, notion_client, create_database, test_records) -> Database[TestRecord]:
        doc = create_database(
            properties={
                "name": {"title": {}},
                "some_id": {"number": {}},
                "some_num": {"number": {}},
                "text": {"rich_text": {}},
                "tags": {
                    "type": "multi_select",
                    "multi_select": {
                        "options": [
                            {"name": "tag_1", "color": "blue"},
                            {"name": "tag_2", "color": "gray"},
                            {"name": "tag_3", "color": "purple"},
                        ]
                    },
                },
            }
        )
        db = Database(TestRecord, doc["id"], notion_client)

        # insert test data
        for i, record in enumerate(test_records):
            test_records[i] = db.create(record)

        return db

    def test_query_by_value_numeric(self, database):
        values = list(database.query_by_value(TestRecord.some_num, 42))
        assert len(values) == 2
        values.sort(key=lambda v: v.some_id)
        assert values[0].some_id == 1
        assert values[1].some_id == 2

    def test_query_by_value_text(self, database):
        values = list(database.query_by_value(TestRecord.text, "foo"))
        assert len(values) == 2
        values.sort(key=lambda v: v.some_id)
        assert values[0].some_id == 1
        assert values[1].some_id == 3

    def test_find_by_id(self, test_records, database):
        record = database.find_by_id(test_records[1].id)

        assert record.id == test_records[1].id
        assert record.name == "record 2"
        assert record.text == "bar"
        assert record.tags == ["tag_2", "tag_3"]
        assert record.some_id == 2

    def test_find_by_id_non_existing_id(self, database):
        assert not database.find_by_id(f"{uuid.uuid4()}")

    def test_find_unique_by_value(self, database):
        record = database.find_unique_by_value(TestRecord.some_id, 1)
        assert record.some_id == 1
        assert record.name == "record 1"
        assert record.text == "foo"
        assert record.tags == ["tag_1", "tag_2"]

    def test_find_unique_by_value_non_existing_value(self, database):
        assert database.find_unique_by_value(TestRecord.some_id, 0) is None
