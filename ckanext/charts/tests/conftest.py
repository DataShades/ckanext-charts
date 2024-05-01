import pytest

from ckanext.charts.cache import drop_disk_cache


@pytest.fixture()
def clean_disk_cache():
    drop_disk_cache()
