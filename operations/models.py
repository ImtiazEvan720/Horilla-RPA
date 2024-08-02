"""
Models for Asset Management System

This module defines Django models to manage assets, their categories, assigning, and requests
within an Asset Management System.
"""
import json
import os
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import time
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company
from employee.models import Employee
from asset.models import Asset
from horilla.models import HorillaModel
from horilla.tasks import create_operation_log

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

logger = logging.getLogger("apscheduler")

def get_current_time():
    now = timezone.now()
    return now.time()

# Get the current directory of the script
current_directory = os.path.dirname(__file__)

# Move up one directory
parent_directory = os.path.dirname(current_directory)

# Configure APScheduler to use the existing TestDB_Horilla.sqlite3 for job storage
database_path = os.path.join(parent_directory, 'TestDB_Horilla.sqlite3')
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{database_path}')
}

scheduler = BackgroundScheduler(jobstores=jobstores)
logger.debug(f"database path {database_path}")

def start_scheduler():
    # Set up the scheduler with the SQLite job store    
    if not scheduler.running:
        try:
            scheduler.start()
            logger.debug("Scheduler started successfully.")
        except Exception as e:
            logger.debug(f"Error starting scheduler: {e}")
    else:
        logger.debug("Scheduler is already running.")


def add_job(job_func, trigger, args, job_id, replace_existing=True):
    scheduler.add_job(
        job_func,
        trigger,
        args=args,
        id=job_id,
        replace_existing=replace_existing
    )
    logger.info(f"Added job {job_id} to scheduler.")

# Define the job function
def schedule_operation_log(operation_id):
    create_operation_log(operation_id)

def schedule_operation_tasks():
    from .models import Operation,add_job

    operations = Operation.objects.all()
    for operation in operations:
        job_id = f'log-operation-{operation.id}'

        trigger = None
        if operation.frequency == "Once":
            trigger = DateTrigger(run_date=timezone.now())
        elif operation.frequency == 'EveryOtherMin':
            trigger = IntervalTrigger(minutes=2)
        elif operation.frequency == "Daily":
            # trigger = CronTrigger(
            #     minute=operation.preferred_time.minute,
            #     hour=operation.preferred_time.hour,
            #     day_of_week='*',
            #     day='*',
            #     month='*'
            # )
            trigger = IntervalTrigger(minutes=3)
        elif operation.frequency == "Weekly":
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='1',
                day='*',
                month='*'
            )
        elif operation.frequency == "Monthly":
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day='1',
                month='*'
            )
        elif operation.frequency == "Yearly":
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day='1',
                month='1'
            )

        if trigger:
            try:
                add_job(schedule_operation_log, trigger, [operation.id], job_id)
            except Exception as e:
                logger.error(f"Failed to add job {job_id}: {e}")


class Operation(HorillaModel):
    MAINTENANCE_SCHEDULE = [
        ("Once",_("Once")),
        ("OnDemand",_("On Demand")),
        ("EveryOtherMin",_("Every Other Min")),
        ("Daily", _("Daily")),
        ("Weekly", _("Weekly")),
        ("Monthly", _("Monthly")),
        ("Yearly", _("Yearly")),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    frequency = models.CharField(choices=MAINTENANCE_SCHEDULE,max_length=100)
    preferred_time = models.TimeField(verbose_name=_("Preferred Time"),default=time(0,0))
    assigned_to = models.ForeignKey(Employee,on_delete=models.PROTECT,null=True, blank=True)
    related_asset = models.ForeignKey(Asset, on_delete=models.PROTECT,null=True, blank=True)

    @classmethod
    def get_default_operation(cls):
        exam, created = cls.objects.get_or_create(
            name='default operation', 
            defaults=dict(description='this is not an exam',frequency='OnDemand',preferred_time=get_current_time(),related_asset= None),
        )
        return exam.id

    def __str__(self):
        return self.name

class OperationLog(HorillaModel):
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT,default=Operation.get_default_operation)
    performed_by = models.ForeignKey(Employee,on_delete=models.PROTECT,null=True, blank=True)
    date = models.DateTimeField(verbose_name=_("Operation Schedule Date"),default=timezone.now)
    notes = models.TextField(null=True, blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.operation.name} - {self.id}"


@receiver(post_save, sender=Operation)
def schedule_operation_logs(sender, instance, **kwargs):

    operation = instance

    scheduler = BackgroundScheduler()    
    job_id = f'log-operation-{operation.id}'

    if operation.frequency == "Once":
        scheduler.add_job(
            schedule_operation_log,
            DateTrigger(run_date=timezone.now()),
            args=[operation.id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_id} for operation {operation.id}")

    elif operation.frequency == 'EveryOtherMin':
        scheduler.add_job(
            schedule_operation_log,
            IntervalTrigger(minutes=2),
            args=[operation.id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_id} for operation {operation.id}")

    elif operation.frequency == "Daily":
        scheduler.add_job(
            schedule_operation_log,
            CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day='*',
                month='*'
            ),
            args=[operation.id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_id} for operation {operation.id}")

    elif operation.frequency == "Weekly":
        scheduler.add_job(
            schedule_operation_log,
            CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='1',
                day='*',
                month='*'
            ),
            args=[operation.id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_id} for operation {operation.id}")

    elif operation.frequency == "Monthly":
        scheduler.add_job(
            schedule_operation_log,
            CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day='1',
                month='*'
            ),
            args=[operation.id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_id} for operation {operation.id}")

    elif operation.frequency == "Yearly":
        scheduler.add_job(
            schedule_operation_log,
            CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day='1',
                month='1'
            ),
            args=[operation.id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_id} for operation {operation.id}")
