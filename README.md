# notion-objects

A Python library that makes it easy to work with notion databases.

## Usage

Suppose your database `tasks` has four fields, the title `Task`, a date range `Date`, and a person `Assigned to`, and a status field `Status`.
You want to transform notion database queries into records of:

```json
{"task": "my task", "date_start": "2022-01-01", "date_end": "2022-01-02", "assigned_to": "Thomas", "status": "In progress"}
```

First, declare a model that contains all the necessary transformations as descriptors:

```python
from notion_objects import *

class Task(NotionObject):
    task = TitleText("Task")
    assigned_to = Person("Assigned to")
    date_start = DateRangeStart("Date")
    date_end = DateRangeEnd("Date")
    status = Status("Status")
```

Now, when you have queried a database, you can instantiate `Task` objects with the results of the API call:

```python
response = requests.post("https://api.notion.com/v1/databases/{database_id}/query", ...)

for item in response.json()['results']:
    t = Task(item)
    print(t.task)  # access attribute values
    print(t.to_dict())  # coverts the record to a dictionary
```
