"""
init.py
"""

from .celery import app as celery_app

__all__ = ("celery_app",)

from horilla import (
    haystack_configuration,
    horilla_apps,
    horilla_context_processors,
    horilla_middlewares,
)
