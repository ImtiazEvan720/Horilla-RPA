"""
Models for Asset Management System

This module defines Django models to manage assets, their categories, assigning, and requests
within an Asset Management System.
"""
from celery import shared_task
import json
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from base.horilla_company_manager import HorillaCompanyManager
from base.models import Company
from employee.models import Employee
from asset.models import Asset
from horilla.models import HorillaModel
from horilla.tasks import create_operation_log

class Operation(HorillaModel):
    MAINTENANCE_SCHEDULE = [
        ("Once",_("Once")),
        ("OnDemand",_("On Demand")),
        ("Daily", _("Daily")),
        ("Weekly", _("Weekly")),
        ("Monthly", _("Monthly")),
        ("Yearly", _("Yearly")),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    frequency = models.CharField(choices=MAINTENANCE_SCHEDULE,max_length=100)
    assigned_to = models.ForeignKey(Employee,on_delete=models.PROTECT,null=True, blank=True)
    related_asset = models.ForeignKey(Asset, on_delete=models.PROTECT,null=True, blank=True)

    @classmethod
    def get_default_operation(cls):
        exam, created = cls.objects.get_or_create(
            name='default operation', 
            defaults=dict(description='this is not an exam',frequency='OnDemand',
            related_asset= None),
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
        # interval = IntervalSchedule.objects.ntervalSchedule.objects.get_or_create(
        # every=interval,
        # defaults={
        #     'period': IntervalSchedule.NEVER,  # Assuming you have a constant like NEVER defined in your model
        # }) 
    elif instance.frequency == "Daily":
        create_operation_log.apply_async((instance.id,), countdown=120)  # 24 hours
        # interval = IntervalSchedule.objects.get_or_create(every=1,period='days')
    elif instance.frequency == "Weekly":
        create_operation_log.apply_async((instance.id,), countdown=604800)  # 7 days
        # interval = IntervalSchedule.objects.get_or_create(every=7,period='days')
    elif instance.frequency == "Monthly":
        create_operation_log.apply_async((instance.id,), countdown=2592000)  # 30 days
        # interval = IntervalSchedule.objects.get_or_create(every=30,period='days')
    elif instance.frequency == "Yearly":
        create_operation_log.apply_async((instance.id,), countdown=31536000)  # 1 year
        # interval = IntervalSchedule.objects.get_or_create(every=365,period='days')
    # Add more logic if needed for OnDemand or other frequencies

    # Retrieve or create the IntervalSchedule object with the desired interval
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