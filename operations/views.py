""""
asset.py

This module is used to """

import json
from datetime import date, datetime
from urllib.parse import parse_qs
from django.utils import timezone

import pandas as pd
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import formats
from django.template.loader import get_template
from weasyprint import HTML

from operations.filters import(
    OperationFilter,
    OperationLogFilter
)

from operations.models import(
    Operation,
    OperationLog
)

from operations.forms import(
    OperationForm,
    OperationlogForm
)

from attendance.methods.group_by import group_by_queryset
from base.methods import (
    closest_numbers,
    filtersubordinates,
    get_key_instances,
    get_pagination,
    sortby,
)
from employee.models import Employee
from base.models import Company
from base.views import paginator_qry
from employee.models import EmployeeWorkInformation
from horilla.decorators import (
    hx_request_required,
    login_required,
    manager_can_enter,
    permission_required,
)
from notifications.signals import notify
from django.db import DatabaseError


@login_required
@hx_request_required
def operation_information(request, operation_id):
    """
    Display information about a specific Asset object.
    Args:
        request: the HTTP request object
        asset_id (int): the ID of the Asset object to retrieve
    Returns:
        A rendered HTML template displaying the information about the requested Asset object.
    """

    operation = Operation.objects.get(id=operation_id)
    context = {"operation": operation}

    return render(request, "operations/operations_information.html", context)

@login_required
@hx_request_required
# @permission_required("operation.delete_operation")
def operation_update(request, operation_id):
    """
    Updates an asset with the given ID.
    If the request method is GET, it displays the form to update the asset. If the
    request method is POST and the form is valid, it updates the asset and
    redirects to the asset list view for the asset's category.
    Args:
    - request: the HTTP request object
    - id (int): the ID of the asset to be updated
    Returns:
    - If the request method is GET, the rendered 'asset_update.html' template
      with the form to update the asset.
    - If the request method is POST and the form is valid, a redirect to the asset
      list view for the asset's category.
    """

    instance = Operation.objects.get(id=operation_id)
    operation_form = OperationForm(instance=instance)
    previous_data = request.GET.urlencode()

    if request.method == "POST":
        operation_form = OperationForm(request.POST, instance=instance)
        if operation_form.is_valid():
            operation_form.save()
            messages.success(request, _("Operation Updated"))
            return HttpResponse("<script>window.location.reload();</script>")
    context = {
        "operation_form": operation_form,
        "pg": previous_data,
    }

    return render(request, "operations/operation_update.html", context=context)


@login_required
@permission_required(perm="operations.delete_operation")
def operation_delete(request, operation_id):
    """Delete the asset with the given id.
    If the asset is currently in use, display an info message and
    redirect to the asset list.
    Otherwise, delete the asset and display a success message.
    Args:
        request: HttpRequest object representing the current request.
        asset_id: int representing the id of the asset to be deleted.
    Returns:
        If the asset is currently in use or the asset list filter is
        applied, render the asset list template
        with the corresponding context.
        Otherwise, redirect to the asset list view for the asset
        category of the deleted asset.
    """
    try:
        operation = Operation.objects.get(id=operation_id)
        task_name = f'log-operation-{operation_id}'
    
        # deleted_count,records = PeriodicTask.objects.filter(name=task_name).delete()
        deleted_count_logs, log_records = OperationLog.objects.filter(operation=operation_id).delete()
        if deleted_count > 0 or deleted_count_logs > 0:
            print(f"Successfully deleted {deleted_count_logs} operations with name '{task_name}'.")                        
        else:
            print(f"No task found with name '{task_name}'.")                        
    except Exception as e:
        # Handle any other unexpected exceptions
        print(f"An unexpected error occurred: {e}")  
        messages.error(request, _(f"An unexpected error occurred: {e}"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    except Operation.DoesNotExist:
        messages.error(request, _("Operation not found"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    try:
        operation.delete()
        messages.success(request, _("Operation deleted successfully"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this asset."))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

@login_required
@hx_request_required
@permission_required(perm="operations.add_operation")
def operation_creation(request):
    """
    Allow a user to create a new AssetCategory object using a form.
    Args:
        request: the HTTP request object
    Returns:
        A rendered HTML template displaying the AssetCategory creation form.
    """
    operation_form = OperationForm()

    if request.method == "POST":
        operation_form = OperationForm(request.POST)
        if operation_form.is_valid():
            operation_form.save()
            messages.success(request, _("Operation created successfully"))
            operation_form = OperationForm()
            return HttpResponse("<script>window.location.reload();</script>")
            # if Operation.objects.filter().count() == 1:
            #     return HttpResponse("<script>window.location.reload();</script>")
    context = {"operation_form": operation_form}
    return render(request, "category/operation_creation.html", context)

@login_required
@hx_request_required
@permission_required(perm="operations.add_operationlog")
def operationlog_creation(request):
    """
    Allow a user to create a new AssetCategory object using a form.
    Args:
        request: the HTTP request object
    Returns:
        A rendered HTML template displaying the AssetCategory creation form.
    """
    operationlog_form = OperationlogForm()

    if request.method == "POST":
        operationlog_form = OperationlogForm(request.POST)
        if operationlog_form.is_valid():
            operationlog_form.save()
            messages.success(request, _("Operation created successfully"))
            operationlog_form = OperationForm()
            return HttpResponse("<script>window.location.reload();</script>")
            # if Operation.objects.filter().count() == 1:
            #     return HttpResponse("<script>window.location.reload();</script>")
    context = {"operationlog_form": operationlog_form}
    return render(request, "category/operationlog_creation.html", context)    

@login_required
def operationlog_update_approval(request,operationlog_id,approved_value):
    """
    Allow a user to create a new AssetCategory object using a form.
    Args:
        request: the HTTP request object
    Returns:
        A rendered HTML template displaying the AssetCategory creation form.
    """

    try:
        # Retrieve the OperationLog instance
        instance = OperationLog.objects.get(id=operationlog_id)

        # Update the approved field based on approved_value
        if approved_value == 'true':
            instance.approved = True
        elif approved_value == 'false':
            instance.approved = False
        else:
            messages.error(request, _("Invalid Params"))
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        # Save the instance
        instance.save()

        # Prepare success response
        # response_data = {
        #     'status': 'success',
        #     'message': 'Operation log updated successfully'
        # }
        messages.error(request, _("Log status changed successfully"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))        

    except OperationLog.DoesNotExist:        
        messages.error(request, _("Operation log not found"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    except Exception as e:        
        messages.error(request, _(str(e)))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    

@login_required 
@permission_required(perm="operations.view_operation")
def operations_dashboard(request):
    """
    This method is used to render the dashboard of the asset module.
    """
    operations = Operation.objects.all()
    operationLogs = OperationLog.objects.all()
    # asset_in_use = Asset.objects.filter(asset_status="In use")
    # asset_requests = AssetRequest.objects.filter(
    #     asset_request_status="Requested", requested_employee_id__is_active=True
    # )
    # requests_ids = json.dumps([instance.id for instance in asset_requests])
    # asset_allocations = AssetAssignment.objects.filter(
    #     asset_id__asset_status="In use", assigned_to_employee_id__is_active=True
    # )
    context = {
        "operations": operations,
        "operationLogs":operationLogs,
    }
    return render(request, "operations/dashboard.html", context)

@login_required 
@permission_required(perm="operations.view_operation")
def operations_list(request):
    """
    This method is used to render the dashboard of the asset module.
    """
    operations = Operation.objects.all()
    # operationLogs = OperationLog.objects.all()
    # asset_in_use = Asset.objects.filter(asset_status="In use")
    # asset_requests = AssetRequest.objects.filter(
    #     asset_request_status="Requested", requested_employee_id__is_active=True
    # )
    # requests_ids = json.dumps([instance.id for instance in asset_requests])
    # asset_allocations = AssetAssignment.objects.filter(
    #     asset_id__asset_status="In use", assigned_to_employee_id__is_active=True
    # )
    context = {
        "operations": operations,
        # "operationLogs":operationLogs,
    }
    return render(request, "operations/operations_list.html", context)

@login_required 
@permission_required(perm="operations.view_operationlog")
def operationlog_list(request):
    """
    This method is used to render the dashboard of the asset module.
    """

    user = request.user  # Assuming 'request' is available in your view

    if user.is_superuser:  # Example permission check
        operationLogs = OperationLog.objects.all()
    else:
        # Assuming `Employee` model is related to Django's built-in `User` model
        # current_employee = get_object_or_404(Employee, user=request.user)
        
        # Filter OperationLog objects where performed_by is the current request user's employee instance
        operationLogs = OperationLog.objects.filter(performed_by=request.user.employee_get)

    paginator = Paginator(operationLogs, 10)  # Show 10 items per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "operationlogs": page_obj,
        # "operationLogs":operationLogs,
    }
    return render(request, "operations/operationlog_list.html", context)

@login_required
@hx_request_required
def operationlog_information(request, operationlog_id):
    """
    Display information about a specific Asset object.
    Args:
        request: the HTTP request object
        asset_id (int): the ID of the Asset object to retrieve
    Returns:
        A rendered HTML template displaying the information about the requested Asset object.
    """

    operationLog = OperationLog.objects.get(id=operationlog_id)
    context = {"operationlog": operationLog}
    
    return render(request, "operations/operationlog_information.html", context)

@login_required
@permission_required(perm="operations.delete_operationlog")
def operationlog_delete(request, operationlog_id):
    """Delete the asset with the given id.
    If the asset is currently in use, display an info message and
    redirect to the asset list.
    Otherwise, delete the asset and display a success message.
    Args:
        request: HttpRequest object representing the current request.
        asset_id: int representing the id of the asset to be deleted.
    Returns:
        If the asset is currently in use or the asset list filter is
        applied, render the asset list template
        with the corresponding context.
        Otherwise, redirect to the asset list view for the asset
        category of the deleted asset.
    """
    try:
        operationlog = OperationLog.objects.get(id=operationlog_id)
    except Operation.DoesNotExist:
        messages.error(request, _("Operation log not found"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    try:
        operationlog.delete()
        messages.success(request, _("Operation log deleted successfully"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this operation log."))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

def operationlog_update(request, operationlog_id):
    """
    Updates an asset with the given ID.
    If the request method is GET, it displays the form to update the asset. If the
    request method is POST and the form is valid, it updates the asset and
    redirects to the asset list view for the asset's category.
    Args:
    - request: the HTTP request object
    - id (int): the ID of the asset to be updated
    Returns:
    - If the request method is GET, the rendered 'asset_update.html' template
      with the form to update the asset.
    - If the request method is POST and the form is valid, a redirect to the asset
      list view for the asset's category.
    """

    instance = OperationLog.objects.get(id=operationlog_id)
    operationlog_form = OperationlogForm(instance=instance)
    previous_data = request.GET.urlencode()

    if request.method == "POST":
        operationlog_form = OperationlogForm(request.POST, instance=instance)
        if operationlog_form.is_valid():
            operationlog_form.save()
            messages.success(request, _("Operation Updated"))
            return HttpResponse("<script>window.location.reload();</script>")
    context = {
        "operationlog_form": operationlog_form,
        "pg": previous_data,
    }

    return render(request, "operations/operationlog_update.html", context=context)
    operation_instance = Operation.objects.get(id=operation_id)

    if request.method == "POST":
        operationlog_instance = OperationLog(operation_instance,request.user.employee_get,timezone.now(),"")
        operationlog_instance.save()
        messages.success(request, _("Log Created"))
        return HttpResponse("<script>window.location.reload();</script>")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def generate_pdf(request):
    # Retrieve data or context needed for your PDF

    user = request.user  # Assuming 'request' is available in your view

    if user.is_superuser:  # Example permission check
        operationLogs = OperationLog.objects.all()
    else:                
        # Filter OperationLog objects where performed_by is the current request user's employee instance
        operationLogs = OperationLog.objects.filter(performed_by=request.user.employee_get)
    
    context = {
        'operation_logs':operationLogs,
        'title': 'Operation Logs',
        'content': 'Operation Logs for Employee ' + request.user.employee_get.get_full_name(),
    }

    # Render HTML template
    template = get_template('operations/pdf_template.html')
    html_content = template.render(context)

    # Generate PDF using WeasyPrint
    pdf_file = HTML(string=html_content).write_pdf()

    # Return PDF response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="sample.pdf"'
    return response

# @login_required
# def clear_operation_logs(operation_id):

#     task_name = f'log-operation-{operation_id}'
#     try :
#         deleted_count,records = PeriodicTask.objects.filter(name=task_name).delete()
#         deleted_count_logs, log_records = OperationLog.objects.filter(operation=operation_id).delete()
#         if deleted_count > 0 or deleted_count_logs > 0:
#             print(f"Successfully deleted {deleted_count} task(s) with name '{task_name}'.")                        
#         else:
#             print(f"No task found with name '{task_name}'.")                    
#     except DatabaseError as e:
#         # Handle any database errors that occur
#         print(f"An error occurred while deleting the periodic task: {e}")        
#     except Exception as e:
#         # Handle any other unexpected exceptions
#         print(f"An unexpected error occurred: {e}")        
