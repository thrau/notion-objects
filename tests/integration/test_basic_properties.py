import datetime

import pytest

from notion_objects import (
    Checkbox,
    Database,
    Date,
    MultiSelect,
    Number,
    Page,
    People,
    RichTextProperty,
    Select,
    Text,
    TitleText,
    rich_text,
)

# TODO: add more properties to test

test_db_properties = {
    "Name": {"title": {}},
    "Description": {"rich_text": {}},
    "In stock": {"checkbox": {}},
    "Food group": {
        "select": {
            "options": [
                {"name": "Vegetable", "color": "green"},
                {"name": "Fruit", "color": "red"},
                {"name": "Protein", "color": "yellow"},
            ]
        }
    },
    "Price": {"number": {"format": "dollar"}},
    "Last ordered": {"date": {}},
    "Store availability": {
        "type": "multi_select",
        "multi_select": {
            "options": [
                {"name": "Duc Loi Market", "color": "blue"},
                {"name": "Rainbow Grocery", "color": "gray"},
                {"name": "Nijiya Market", "color": "purple"},
                {"name": "Gus'''s Community Market", "color": "yellow"},
            ]
        },
    },
    "+1": {"people": {}},
}


class FoodRecord(Page):
    name = TitleText("Name")
    description = RichTextProperty("Description")
    in_stock = Checkbox("In stock")
    food_group = Select("Food group")
    Price = Number()
    last_ordered = Date("Last ordered")
    store_availability = MultiSelect("Store availability")
    upvoted = People("+1")
    description_plain = Text("Description")


@pytest.fixture()
def food_db(notion_client, create_database) -> Database[FoodRecord]:
    database = create_database(properties=test_db_properties)

    return Database(FoodRecord, database["id"], notion_client)


def test_create_and_list_records(food_db):
    now = datetime.date(year=1969, month=4, day=20)
    food_db.create(
        FoodRecord.new(
            name="My New Food Record",
            description=rich_text.RichText(
                "hot food record", link="https://example.com", color="red", bold=True
            ),
            in_stock=True,
            Price=123.45,
            last_ordered=now,
            food_group="Fruit",
            store_availability=["Duc Loi Market", "Rainbow Grocery"],
        )
    )
    food_db.create(
        FoodRecord.new(
            name="My empty food record",
        )
    )

    records = list(food_db)
    assert len(records) == 2

    assert records[0].name == "My empty food record"
    assert records[0].in_stock is False
    assert records[0].food_group is None
    assert records[0].store_availability == []
    assert records[0].Price is None
    assert records[0].last_ordered is None
    assert records[0].description == []
    assert records[0].description_plain == ""

    assert records[1].name == "My New Food Record"
    assert records[1].in_stock
    assert records[1].food_group == "Fruit"
    assert records[1].store_availability == ["Duc Loi Market", "Rainbow Grocery"]
    assert records[1].Price == 123.45
    assert records[1].last_ordered == now
    assert records[1].description_plain == "hot food record"
    assert records[1].description[0].to_dict() == {
        "annotations": {
            "bold": True,
            "code": False,
            "color": "red",
            "italic": False,
            "strikethrough": False,
            "underline": False,
        },
        "href": "https://example.com/",
        "plain_text": "hot food record",
        "text": {"content": "hot food record", "link": {"url": "https://example.com/"}},
        "type": "text",
    }


def test_create_to_dict(food_db):
    now = datetime.date(year=1969, month=4, day=20)

    record = food_db.create(
        FoodRecord.new(
            name="My New Food Record",
            description=rich_text.RichText(
                "hot food record", link="https://example.com", color="red", bold=True
            ),
            in_stock=True,
            last_ordered=now,
            Price=123.45,
            food_group="Fruit",
            store_availability=["Duc Loi Market", "Rainbow Grocery"],
        )
    )

    doc = record.to_dict()
    # remove dynamic properties we can't match directly
    doc.pop("created_time")
    doc.pop("last_edited_time")
    doc.pop("id")

    assert doc == {
        "Price": 123.45,
        "description": "hot food record",
        "description_plain": "hot food record",
        "food_group": "Fruit",
        "in_stock": True,
        "last_ordered": now,
        "name": "My New Food Record",
        "store_availability": ["Duc Loi Market", "Rainbow Grocery"],
        "upvoted": [],
    }
