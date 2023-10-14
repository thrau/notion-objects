# notion-objects

[![Build Status](https://github.com/thrau/notion-objects/actions/workflows/test.yml/badge.svg)](https://github.com/thrau/notion-objects/actions/workflows/test.yml)
[![PyPI Version](https://badge.fury.io/py/notion-objects.svg)](https://badge.fury.io/py/notion-objects)
[![PyPI License](https://img.shields.io/pypi/l/notion-objects.svg)](https://img.shields.io/pypi/l/notion-objects.svg)
[![Codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python library that makes it easy to work with notion databases, built on top of [notion-sdk-py](https://github.com/ramnes/notion-sdk-py).
It provides a higher-level API with a data mapper, allowing you to define custom mappings between notion database records and your Python objects.

With notion-objects you can:
* [Transform properties](#defining-models)
* [Query databases](#querying-databases)
* [Update records](#updating-records)
* [Create records](#creating-records)

## User guide

### Defining models

Suppose your database `tasks` has four fields, the title `Task`, a date range `Date`, and a person `Assigned to`, and a status field `Status`.
You want to transform notion database queries into records of:

```json
{
  "task": "my task",
  "date_start": "2022-01-01",
  "date_end": "2022-01-02",
  "assigned_to": "Thomas",
  "status": "In progress"
}
```

First, declare a model that contains all the necessary transformations as descriptors:

```python
from notion_objects import *

class Task(NotionObject):
    task = TitleText("Task")
    assigned_to = Person("Assigned to")
    date_start = DateRangeStart("Date")
    date_end = DateRangeEnd("Date")
    closed_at = Date("Closed at")
    status = Status("Status")
```

Now, when you have queried a database, you can instantiate `Task` objects with the results of the API call:

```python
response = requests.post("https://api.notion.com/v1/databases/{database_id}/query", ...)

for item in response.json()['results']:
    t = Task(item)
    print(t.task)  # access attribute values
    print(t.to_json())  # prints the record in the json format show earlier
```

### Querying Databases

notion-objects adds data-mapping around [notion-sdk-py](https://github.com/ramnes/notion-sdk-py). The `Database` class
is uses a type parameter to map notion objects to the data models you defined.

Here's a code snippet showing how to iterate over all pages in a databases that were updated after 2022-10-08, using
our built-in `Page` model that holds the root page attributes.

```python
from notion_client import Client
from notion_objects import Database, Page

notion = Client(auth=os.environ['NOTION_TOKEN'])

database: Database[Page] = Database(Page, database_id="123456789abcdef1234567890abcdef1", client=notion)

result = database.query({
    "filter": {
        "timestamp": "last_edited_time",
        "last_edited_time": {
            "after": "2022-10-08"
        }
    }
})
for page in result:
    print(page.id, page.created_time, page.last_edited_time)
```

You could also use `DynamicNotionObject` if you're too lazy to create a model for your database. notion-objects will map
the data types in a best-effort way. You can also iterate directly over the database to fetch all records:

```python
from notion_objects import Database, DynamicNotionObject

database = Database(DynamicNotionObject, ...)

for record in database:
    print(record.to_json())  # will print your database record as JSON
```

**NOTE** not all types have yet been implemented. Type mapping is very rudimentary.

### Updating records

You can update database records by simply calling attributes with normal python assignments.
The data mapper will map the types correctly to Notion's internal format.
You can then call `Database.update(...)` to run an update API call.
notion-objects keeps track of all the changes that were made to the object, and only sends the changes.

```python
database: Database[Task] = Database(Task, ...)

task = database.find_by_id("...")
task.status = "Done"
task.closed_at = datetime.utcnow()
database.update(task)
```

**Note** not all properties can be set yet.

### Creating records

Similarly, you can also create new pages.
You can use `NotionObject.new()` on any subclass to create new unmanaged instances of that type.
Then, call `Database.create(...)` to create a new item in the database.

```python
database: Database[Task] = Database(Task, ...)

task = Task.new()
task.task = "My New Task"
task.status = "In progress"
task.assigned_to = "6aa4d3cd-3928-4f61-9072-f74a3ebfc3ca"

task = database.create(task)
print(task.id)  # will print the page ID that was created
```
