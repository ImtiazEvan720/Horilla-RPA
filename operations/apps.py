"""
Module: apps.py
Description: Configuration for the 'asset' app.
"""

from django.apps import AppConfig
import logging

class OperationConfig(AppConfig):
    """
    Class: AssetConfig
    Description: Configuration class for the 'asset' app.

    Attributes:
        default_auto_field (str): Default auto-generated field type for primary keys.
        name (str): Name of the app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "operations"

    def ready(self):    
        
        logger = logging.getLogger('apscheduler')
        logger.debug('App starting!!')
        from .models import start_scheduler
        start_scheduler()  # Initialize the scheduler
        from .models import schedule_operation_tasks    
        schedule_operation_tasks()  # Initialize the scheduler
