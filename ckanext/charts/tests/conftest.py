import pytest

from ckanext.charts.cache import drop_file_cache


@pytest.fixture()
def clean_file_cache():
    drop_file_cache()
