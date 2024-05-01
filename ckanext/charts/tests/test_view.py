import pytest

import ckan.lib.helpers as h
from ckan.tests import factories


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestAllowedViews:
    """Test that the allowed views are correctly returned based on the
    datastore_active field of the resource. For now we're working only
    with resources that are stored in datastore."""

    def test_not_in_datastore(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset["id"])

        assert not h.get_allowed_view_types(resource, dataset)

    def test_in_datastore(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset["id"], datastore_active=True)

        assert h.get_allowed_view_types(resource, dataset) == [
            ("charts_view", "Chart", "chart-line")
        ]
