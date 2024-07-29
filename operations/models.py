"""
Models for Asset Management System

This module defines Django models to manage assets, their categories, assigning, and requests
within an Asset Management System.
"""
from celery import shared_task
import json
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule

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

def get_current_time():
    now = timezone.now()
    return now.time()

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
    preferred_time = models.TimeField(verbose_name=_("Preferred Time"),default=get_current_time)
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

    if instance.frequency == "Once":
        create_operation_log.apply_async((instance.id,), countdown=0)    
    elif instance.frequency == 'EveryOtherMin':
        interval_schedule, created = IntervalSchedule.objects.get_or_create(
            every=2,  # Adjust as per your interval definition
            defaults={
                'period': IntervalSchedule.MINUTES,  # Assuming DAYS is a constant in your model
            }
        )

        PeriodicTask.objects.update_or_create(
        interval=interval_schedule,
        name=f'log-operation-{instance.id}',
        task='horilla.tasks.create_operation_log',
        args=json.dumps([instance.id]),
        )
    elif instance.frequency == "Daily":        
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(instance.preferred_time.minute),
            hour=str(instance.preferred_time.hour),
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'            
        )

        PeriodicTask.objects.update_or_create(
        crontab=crontab_schedule,
        name=f'log-operation-{instance.id}',
        task='horilla.tasks.create_operation_log',
        args=json.dumps([instance.id]),
        )
    elif instance.frequency == "Weekly":
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(instance.preferred_time.minute),
            hour=str(instance.preferred_time.hour),
            day_of_week='1',
            day_of_month='*',
            month_of_year='*'            
        )

        PeriodicTask.objects.update_or_create(
        crontab=crontab_schedule,
        name=f'log-operation-{instance.id}',
        task='horilla.tasks.create_operation_log',
        args=json.dumps([instance.id]),
        )

    elif instance.frequency == "Monthly":
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(instance.preferred_time.minute),
            hour=str(instance.preferred_time.hour),
            day_of_week='*',
            day_of_month='1',
            month_of_year='*'            
        )

        PeriodicTask.objects.update_or_create(
        crontab=crontab_schedule,
        name=f'log-operation-{instance.id}',
        task='horilla.tasks.create_operation_log',
        args=json.dumps([instance.id]),
        )

    elif instance.frequency == "Yearly":
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(instance.preferred_time.minute),
            hour=str(instance.preferred_time.hour),
            day_of_week='*',
            day_of_month='*',
            month_of_year='1'
        )

        PeriodicTask.objects.update_or_create(
        crontab=crontab_schedule,
        name=f'log-operation-{instance.id}',
        task='horilla.tasks.create_operation_log',
        args=json.dumps([instance.id]),
        )
