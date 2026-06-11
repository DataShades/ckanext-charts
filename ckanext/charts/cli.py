from __future__ import annotations

import click

from ckanext.charts import cache

__all__ = ["charts"]


@click.group(short_help="ckanext-charts management commands")
def charts():
    pass


@charts.command("clear-expired-cache")
def clear_expired_cache():
    """Remove expired files from the chart file cache.

    Intended to be run periodically (e.g. from cron) instead of pruning on
    every worker startup.
    """
    cache.remove_expired_file_cache()
    click.secho("Expired chart cache files have been removed", fg="green")


@charts.command("clear-cache")
def clear_cache():
    """Remove all chart caches (Redis and file)."""
    cache.invalidate_all_cache()
    click.secho("All chart caches have been cleared", fg="green")
