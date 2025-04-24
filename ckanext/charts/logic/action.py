from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan.types import Action, Context, DataDict

from ckanext.charts import fetchers


@tk.chained_action
def resource_view_create(
    next_action: Action,
    context: Context,
    data_dict: DataDict,
):
    """Ensures chart cache is updated after view creation.

    During chart creation, data is initially cached using the resource_id. Once
    the view is created and an ID is available, update the cache key to use the
    view_id and remove the old cache.
    """
    if context.get("preview"):
        return next_action(context, data_dict)

    results = next_action(context, data_dict)

    if results["view_type"] in {"charts_builder_view", "charts_view"}:
        fetchers.DatastoreDataFetcher(results["resource_id"]).update_view_id(
            results["id"],
        )
    return results
