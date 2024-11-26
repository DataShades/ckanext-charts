import pandas as pd
import pytest

from ckanext.charts.cache import drop_file_cache


@pytest.fixture()
def clean_file_cache():
    drop_file_cache()


@pytest.fixture()
def data_frame():
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "surname": ["Bing", "Right"],
            "age": [25, 30],
        },
    )
