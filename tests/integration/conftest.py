import copy
import os
import time
import uuid

import pytest
from notion_client import Client

import notion_objects


@pytest.fixture(scope="session")
def notion_client():
    return Client(auth=os.environ["NOTION_OBJECTS_TOKEN"])


@pytest.fixture(scope="session")
def test_run_database_id():
    return os.environ["NOTION_OBJECTS_TEST_DATABASE"]


@pytest.fixture(scope="session")
def test_run_page(notion_client, test_run_database_id):
    name = f"pytest-{int(time.time() * 1000)}"

    page = notion_client.pages.create(
        parent={
            "database_id": test_run_database_id,
        },
        properties={
            "Name": {"title": [{"text": {"content": name}}]},
            "Version": {"rich_text": [{"text": {"content": f"{notion_objects.__version__}"}}]},
        },
    )

    yield page

    # notion_client.pages.update(page["id"], archived=True)


@pytest.fixture()
def create_database(notion_client, test_run_page):
    def _create(**kwargs):
        kwargs = copy.deepcopy(kwargs)

        if "parent" not in kwargs:
            kwargs["parent"] = {
                "type": "page_id",
                "page_id": test_run_page["id"],
            }

        if "title" not in kwargs:
            name = f"pytest-test-database-{uuid.uuid4()}"
            kwargs["title"] = [{"text": {"content": name, "link": None}}]

        return notion_client.databases.create(**kwargs)

    yield _create
