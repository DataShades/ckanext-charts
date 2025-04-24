from __future__ import annotations

import os
import random
from typing import Any

from ckan.tests.factories import Resource
from ckan.tests.helpers import call_action


def create_resource_with_datastore(row_count: int = 100) -> dict[str, Any]:
    """Create a resource and upload it into datastore"""
    resource = Resource()

    fields = [
        {"id": "name", "type": "text"},
        {"id": "age", "type": "int"},
        {"id": "city", "type": "text"},
        {"id": "score", "type": "int"},
    ]

    records = [
        {
            "name": f"Name {i}",
            "age": str(20 + i),
            "city": f"City {i % 5}",
            "score": i,
        }
        for i in range(row_count)
    ]

    # Shuffle the records to ensure they're not pre-sorted
    random.shuffle(records)

    call_action(
        "datastore_create",
        resource_id=resource["id"],
        fields=fields,
        records=records,
        force=True,
    )

    return resource


def get_file_content(fmt: str) -> bytes:
    """Return the content of a sample file"""
    file_path = os.path.join(os.path.dirname(__file__), "data", f"sample.{fmt}")

    with open(file_path, mode="rb") as file:
        return file.read()


def get_file_path(file_name: str) -> str:
    return os.path.join(os.path.dirname(__file__), "data", file_name)
