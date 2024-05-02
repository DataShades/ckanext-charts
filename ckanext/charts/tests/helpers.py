from __future__ import annotations

import os

from ckan.tests.factories import Resource
from ckan.tests.helpers import call_action


def create_resource_with_datastore():
    """Create a resource and upload it into datastore"""
    resource = Resource()

    call_action(
        "datastore_create",
        resource_id=resource["id"],
        fields=[{"id": "name", "type": "text"}, {"id": "age", "type": "text"}],
        records=[{"name": "A", "age": "1"}, {"name": "B", "age": "2"}],
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
