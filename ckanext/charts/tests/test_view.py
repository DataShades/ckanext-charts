# encoding: utf-8

import pytest
from ckan.common import config

from urllib.parse import urljoin

import ckan.lib.helpers as h
import ckanext.textview.plugin as plugin
from ckan.tests import factories


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestAllowedViews:

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
