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
from datetime import time,date
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company
from employee.models import Employee
from asset.models import Asset
from horilla.models import HorillaModel
from horilla.tasks import create_operation_log
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

import logging

logger = logging.getLogger("scheduler")


def get_day_of_week_index(day):
    weekdays = ["sun","mon","tue","wed","thu","fri","sat","sun"]
    return weekdays.index(day)

def get_current_time():
    now = timezone.now()
    return now.time()

    scheduler.add_job(
        job_func,
        trigger,
        args=args,
        id=job_id,
        replace_existing=replace_existing
    )
    logger.info(f"Added job {job_id} to scheduler.")

# Define the job function
# def schedule_operation_log(operation_id):
#     create_operation_log(operation_id)

# def schedule_operation_tasks():
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
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day='*',
                month='*'
            )            
        elif operation.frequency == "Weekly":
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week=get_day_of_week_index(operation.day_of_week),
                day='*',
                month='*'
            )
        elif operation.frequency == "Monthly":
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day=operation.day_of_month,
                month='*'
            )
        elif operation.frequency == "Yearly":
            trigger = CronTrigger(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day=operation.preferred_date.day,
                month=operation.preferred_date.month
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

    DAYS_OF_WEEK = [
        ("mon", _('Monday')),
        ("tue", _('Tuesday')),
        ("wed", _('Wednesday')),
        ("thu", _('Thursday')),
        ("fri", _('Friday')),
        ("sat", _('Saturday')),
        ("sun", _('Sunday')),
    ]

    # Define choices for days of the month (1 to 30)
    DAYS_OF_MONTH = [(i, str(i)) for i in range(1, 31)]
    

    name = models.CharField(max_length=100)
    description = models.TextField()
    frequency = models.CharField(choices=MAINTENANCE_SCHEDULE,max_length=100)
    preferred_time = models.TimeField(verbose_name=_("Preferred Time"),default=time(0,0))
    preferred_date = models.DateField(null=True, blank=True)
    day_of_week = models.CharField(max_length=3,choices=DAYS_OF_WEEK,default='mon',null=True, blank=True)
    day_of_month = models.IntegerField(choices=DAYS_OF_MONTH,default=1,null=True, blank=True)

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
def schedule_operation_logs(sender, instance,created, **kwargs):

    operation = instance     
    job_id = f'log-operation-{operation.id}'

    if created:
        logger.info("New Operation!!")
    else:
        logger.info("Existing Operation Update!!")
        PeriodicTask.objects.filter(name=job_id).delete()
    
    try:
        if operation.frequency == "Once":
            create_operation_log.apply_async((operation.id,), countdown=0)
            logger.info(f"Scheduled job {job_id} for operation {operation.id}")

        elif operation.frequency == 'EveryOtherMin':
            interval_schedule, created = IntervalSchedule.objects.get_or_create(
                every=2,  # Adjust as per your interval definition
                defaults={
                    'period': IntervalSchedule.MINUTES,  # Assuming DAYS is a constant in your model
                }
            )
    
            PeriodicTask.objects.update_or_create(
                interval=interval_schedule,
                name=f'log-operation-{operation.id}',
                task='horilla.tasks.create_operation_log',
                args=json.dumps([operation.id]),
            )
            logger.info(f"Scheduled job {job_id} for operation {operation.id}")

        elif operation.frequency == "Daily":
            crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=str(instance.preferred_time.minute),
                hour=str(instance.preferred_time.hour),
                day_of_week='*',
                day_of_month='*',
                month_of_year='*'            
            )
    
            PeriodicTask.objects.update_or_create(
                crontab=crontab_schedule,
                name=f'log-operation-{operation.id}',
                task='horilla.tasks.create_operation_log',
                args=json.dumps([operation.id]),
            )
            logger.info(f"Scheduled job {job_id} for operation {operation.id}")

        elif operation.frequency == "Weekly":           
            
            crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week=get_day_of_week_index(operation.day_of_week),
                day_of_month='*',
                month_of_year='*'            
            )
        
            PeriodicTask.objects.update_or_create(
                crontab=crontab_schedule,
                name=f'log-operation-{operation.id}',
                task='horilla.tasks.create_operation_log',
                args=json.dumps([operation.id]),
            )
            logger.info(f"Scheduled job {job_id} for operation {operation.id}")

        elif operation.frequency == "Monthly":
            crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day_of_month= operation.day_of_month,
                month_of_year='*'            
            )
        
            PeriodicTask.objects.update_or_create(
                crontab=crontab_schedule,
                name=f'log-operation-{operation.id}',
                task='horilla.tasks.create_operation_log',
                args=json.dumps([operation.id]),
            )
            logger.info(f"Scheduled job {job_id} for operation {operation.id}")

        elif operation.frequency == "Yearly":
            crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=operation.preferred_time.minute,
                hour=operation.preferred_time.hour,
                day_of_week='*',
                day_of_month= operation.preferred_date.day,
                month_of_year=operation.preferred_date.month            
            )
        
            PeriodicTask.objects.update_or_create(
                crontab=crontab_schedule,
                name=f'log-operation-{operation.id}',
                task='horilla.tasks.create_operation_log',
                args=json.dumps([operation.id]),
            )
            logger.info(f"Scheduled job {job_id} for operation {operation.id}")
    except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")