"""
forms.py
Asset Management Forms

This module contains Django ModelForms for handling various aspects of asset management,
including asset creation, allocation, return, category assignment, and batch handling.
"""

import uuid
from datetime import date,datetime
from django.utils import timezone

from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.forms import TextInput,DateTimeInput,TimeInput
from base import thread_local_middleware
from django_flatpickr.widgets import DatePickerInput, TimePickerInput, DateTimePickerInput 


# from asset.models import (
#     Asset,
#     AssetAssignment,
#     AssetCategory,
#     AssetDocuments,
#     AssetLot,
#     AssetReport,
#     AssetRequest,
# )

from operations.models import(
    Operation,
    OperationLog
)

from base.forms import ModelForm
from base.methods import reload_queryset
from employee.forms import MultipleFileField
from employee.models import Employee

class OperationForm(ModelForm):

    class Meta:
        model = Operation
        fields = "__all__"
        exclude = ["is_active"]
        widgets = {
            "preferred_time": TimeInput(attrs={'id':'timepicker','placeholder':'Select time'},format="%H:%M"),
            "frequency": forms.Select(attrs={'id': 'frequency-field'}),   
            "preferred_date" : TextInput(attrs={'id':'datepicker','class': 'form-control', 'type':'date'})
        }

class OperationlogForm(ModelForm):

    class Meta:
        model = OperationLog
        fields = "__all__"
        exclude = ["is_active"]
        widgets = {
            "date": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.get('initial', {})
        request = getattr(thread_local_middleware._thread_locals, "request", None)
        initial['date'] = timezone.now()
        initial['performed_by'] = request.user.employee_get
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
