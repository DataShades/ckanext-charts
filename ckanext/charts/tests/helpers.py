from __future__ import annotations

import os


def get_file_content(fmt: str) -> bytes:
    """Return the content of a sample file"""
    file_path = os.path.join(os.path.dirname(__file__), "data", f"sample.{fmt}")

    with open(file_path, mode="rb") as file:
        return file.read()


def get_file_path(file_name: str) -> str:
    return os.path.join(os.path.dirname(__file__), "data", file_name)
