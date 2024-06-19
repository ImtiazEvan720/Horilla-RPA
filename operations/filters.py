"""
Module containing custom filter classes for various models.
"""

import uuid

import django_filters
from django import forms
from django_filters import FilterSet

from base.methods import reload_queryset
from horilla.filters import filter_by_name

from .models import Operation,OperationLog


class CustomFilterSet(FilterSet):
    """
    Custom FilterSet class that applies specific CSS classes to filter
    widgets.

    The class applies CSS classes to different types of filter widgets,
    such as NumberInput, EmailInput, TextInput, Select, Textarea,
    CheckboxInput, CheckboxSelectMultiple, and ModelChoiceField. The
    CSS classes are applied to enhance the styling and behavior of the
    filter widgets.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reload_queryset(self.form.fields)
        for field_name, field in self.form.fields.items():
            filter_widget = self.filters[field_name]
            widget = filter_widget.field.widget
            if isinstance(
                widget, (forms.NumberInput, forms.EmailInput, forms.TextInput)
            ):
                field.widget.attrs.update({"class": "oh-input w-100"})
            elif isinstance(widget, (forms.Select,)):
                field.widget.attrs.update(
                    {
                        "class": "oh-select oh-select-2",
                    }
                )
            elif isinstance(widget, (forms.Textarea)):
                field.widget.attrs.update({"class": "oh-input w-100"})
            elif isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                ),
            ):
                filter_widget.field.widget.attrs.update(
                    {"class": "oh-switch__checkbox"}
                )
            elif isinstance(widget, (forms.ModelChoiceField)):
                field.widget.attrs.update(
                    {
                        "class": "oh-select oh-select-2 ",
                    }
                )
            elif isinstance(widget, (forms.DateField)):
                field.widget.attrs.update({"type": "date", "class": "oh-input  w-100"})
            if isinstance(field, django_filters.CharFilter):
                field.lookup_expr = "icontains"


class OperationFilter(CustomFilterSet):
    """
    Custom filter set for Asset instances.
    """

    class Meta:
        """
        A nested class that specifies the configuration for the filter.
            model(class): The Asset model is used to filter.
            fields (str): A special value "__all__" to include all fields
                          of the model in the filter.
        """

        model = Operation
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(OperationFilter, self).__init__(*args, **kwargs)
        for visible in self.form.visible_fields():
            visible.field.widget.attrs["id"] = str(uuid.uuid4())

class OperationLogFilter(CustomFilterSet):
    """
    Custom filter set for Asset instances.
    """

    class Meta:
        """
        A nested class that specifies the configuration for the filter.
            model(class): The Asset model is used to filter.
            fields (str): A special value "__all__" to include all fields
                          of the model in the filter.
        """

        model = OperationLog
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(OperationLogFilter, self).__init__(*args, **kwargs)
        for visible in self.form.visible_fields():
            visible.field.widget.attrs["id"] = str(uuid.uuid4())            
