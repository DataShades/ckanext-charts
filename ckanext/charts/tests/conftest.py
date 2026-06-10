import pandas as pd
import pytest
import random
from typing import Any
from collections.abc import Callable

import factory
from pytest_factoryboy import register

from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.charts.cache import drop_file_cache


@pytest.fixture
def clean_file_cache():
    drop_file_cache()


@pytest.fixture
def data_frame():
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "surname": ["Bing", "Right"],
            "age": [25, 30],
        },
    )


@pytest.fixture
def map_data_frame():
    return pd.DataFrame(
        {
            "country": ["USA", "UKR"],
            "population": [100, 200],
        },
    )


@register(_name="dataset")
class DatasetFactory(factories.Dataset):
    owner_org = factory.LazyFunction(lambda: factories.Organization()["id"])
    private = False


@pytest.fixture
def resource_with_datastore_factory(
    dataset: dict[str, Any],
) -> Callable[..., dict[str, Any]]:
    def _factory(row_count: int = 100) -> dict[str, Any]:
        resource = factories.Resource(package_id=dataset["id"], datastore_active=True)

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

    return _factory


@pytest.fixture
def resource(
    resource_with_datastore_factory: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    return resource_with_datastore_factory()
