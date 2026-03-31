from __future__ import annotations

from typing import Any

import ckan.plugins as p
from ckan import types

from ckanext.charts import cache


class ResourceController(p.SingletonPlugin):
    p.implements(p.IResourceController, inherit=True)

    def before_resource_delete(
        self,
        context: types.Context,
        resource: dict[str, Any],
        resources: list[dict[str, Any]],
    ) -> None:
        cache.invalidate_resource_cache(resource["id"])

    def after_resource_update(
        self,
        context: types.Context,
        resource: dict[str, Any],
    ) -> None:
        cache.invalidate_resource_cache(resource["id"])
