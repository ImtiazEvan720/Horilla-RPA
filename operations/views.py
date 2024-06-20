""""
asset.py

This module is used to """

import json
from datetime import date, datetime
from urllib.parse import parse_qs

import pandas as pd
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import formats

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
@permission_required(perm="operation.delete_operation")
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
    except Operation.DoesNotExist:
        messages.error(request, _("Operation not found"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    # asset_cat_id = asset.asset_category_id.id
    # status = asset.asset_status
    # asset_list_filter = request.GET.get("asset_list")
    # asset_allocation = AssetAssignment.objects.filter(asset_id=asset).first()
    # if asset_list_filter:
    #     # if the asset deleted is from the filtered list of asset
    #     asset_under = "asset_filter"
    #     assets = Asset.objects.all()
    #     previous_data = request.GET.urlencode()
    #     asset_filtered = AssetFilter(request.GET, queryset=assets)
    #     asset_list = asset_filtered.qs
    #     paginator = Paginator(asset_list, 20)
    #     page_number = request.GET.get("page")
    #     page_obj = paginator.get_page(page_number)
    #     context = {
    #         "assets": page_obj,
    #         "pg": previous_data,
    #         "asset_category_id": asset.asset_category_id.id,
    #         "asset_under": asset_under,
    #     }
    #     if status == "In use":
    #         messages.info(request, _("Asset is in use"))
    #         return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    #     elif asset_allocation:
    #         # if this asset is used in any allocation
    #         messages.error(request, _("Asset is used in allocation!."))
    #         return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    try:
        operation.delete()
        messages.success(request, _("Operation deleted successfully"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this asset."))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

@login_required
@hx_request_required
@permission_required(perm="operation.add_operation")
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
@permission_required(perm="operation.add_operationlog")
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
@permission_required(perm="operation.view_operation")
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
@permission_required(perm="operation.view_operation")
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
@permission_required(perm="operationlog.view_operation")
def operationlog_list(request):
    """
    This method is used to render the dashboard of the asset module.
    """
    operationLogs = OperationLog.objects.all()
    context = {
        "operationlogs": operationLogs,
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
     # Format datetime field including time
    if operationLog.date:
        formatted_date = operationLog.date.strftime("%m/%d/%Y, %H:%M")
    else:
        formatted_date = ""
    context = {"operationlog": operationLog,"formatted_date":formatted_date}
    
    return render(request, "operations/operationlog_information.html", context)

# @login_required
# @permission_required(perm="asset.view_assetcategory")
# def asset_available_chart(request):
#     """
#     This function returns the response for the available asset chart in the asset dashboard.
#     """
#     asset_available = Asset.objects.filter(asset_status="Available")
#     asset_unavailable = Asset.objects.filter(asset_status="Not-Available")
#     asset_in_use = Asset.objects.filter(asset_status="In use")

#     labels = ["In use", "Available", "Not-Available"]
#     dataset = [
#         {
#             "label": _("asset"),
#             "data": [len(asset_in_use), len(asset_available), len(asset_unavailable)],
#         },
#     ]

#     response = {
#         "labels": labels,
#         "dataset": dataset,
#         "message": _("Oops!! No Asset found..."),
#         "emptyImageSrc": "/static/images/ui/asset.png",
#     }
#     return JsonResponse(response)


# @login_required
# @permission_required(perm="operation.view_operation")
# def asset_category_chart(request):
#     """
#     This function returns the response for the asset category chart in the asset dashboard.
#     """
#     asset_categories = AssetCategory.objects.all()
#     data = []
#     for asset_category in asset_categories:
#         category_count = 0
#         category_count = len(asset_category.asset_set.filter(asset_status="In use"))
#         data.append(category_count)

#     labels = [category.asset_category_name for category in asset_categories]
#     dataset = [
#         {
#             "label": _("assets in use"),
#             "data": data,
#         },
#     ]

#     response = {
#         "labels": labels,
#         "dataset": dataset,
#         "message": _("Oops!! No Asset found..."),
#         "emptyImageSrc": "/static/images/ui/asset.png",
#     }
#     return JsonResponse(response)


# @login_required
# @permission_required(perm="asset.view_assetassignment")
# def asset_history(request):
#     """
#     This function is responsible for loading the asset history view

#     Args:


#     Returns:
#         returns asset history view template
#     """
#     previous_data = request.GET.urlencode() + "&returned_assets=True"
#     asset_assignments = AssetHistoryFilter({"returned_assets": "True"}).qs.order_by(
#         "-id"
#     )
#     data_dict = parse_qs(previous_data)
#     get_key_instances(AssetAssignment, data_dict)
#     asset_assignments = paginator_qry(asset_assignments, request.GET.get("page"))
#     requests_ids = json.dumps(
#         [instance.id for instance in asset_assignments.object_list]
#     )
#     context = {
#         "asset_assignments": asset_assignments,
#         "f": AssetHistoryFilter(),
#         "filter_dict": data_dict,
#         "gp_fields": AssetHistoryReGroup().fields,
#         "pd": previous_data,
#         "requests_ids": requests_ids,
#     }
#     return render(request, "asset_history/asset_history_view.html", context)


# @login_required
# @permission_required(perm="asset.view_assetassignment")
# def asset_history_single_view(request, asset_id):
#     """
#     this method is used to view details of individual asset assignments

#     Args:
#         request (HTTPrequest): http request
#         asset_id (int): ID of the asset assignment

#     Returns:
#         html: Returns asset history single view template
#     """
#     asset_assignment = get_object_or_404(AssetAssignment, id=asset_id)
#     context = {"asset_assignment": asset_assignment}
#     requests_ids_json = request.GET.get("requests_ids")
#     if requests_ids_json:
#         requests_ids = json.loads(requests_ids_json)
#         previous_id, next_id = closest_numbers(requests_ids, asset_id)
#         context["requests_ids"] = requests_ids_json
#         context["previous"] = previous_id
#         context["next"] = next_id
#     return render(
#         request,
#         "asset_history/asset_history_single_view.html",
#         context,
#     )


# @login_required
# @permission_required(perm="asset.view_assetassignment")
# def asset_history_search(request):
#     """
#     This method is used to filter the asset history view or to group by the datas.

#     Args:
#         request (HTTPrequest):http request

#     Returns:
#         returns asset history list or group by
#     """
#     previous_data = request.GET.urlencode()
#     asset_assignments = AssetHistoryFilter(request.GET).qs.order_by("-id")
#     asset_assignments = sortby(request, asset_assignments, "sortby")
#     template = "asset_history/asset_history_list.html"
#     field = request.GET.get("field")
#     if field != "" and field is not None:
#         asset_assignments = group_by_queryset(
#             asset_assignments, field, request.GET.get("page"), "page"
#         )
#         template = "asset_history/group_by.html"
#         list_values = [entry["list"] for entry in asset_assignments]
#         id_list = []
#         for value in list_values:
#             for instance in value.object_list:
#                 id_list.append(instance.id)

#         requests_ids = json.dumps(list(id_list))
#     else:
#         asset_assignments = paginator_qry(asset_assignments, request.GET.get("page"))

#         requests_ids = json.dumps(
#             [instance.id for instance in asset_assignments.object_list]
#         )
#     data_dict = parse_qs(previous_data)
#     get_key_instances(AssetAssignment, data_dict)

#     return render(
#         request,
#         template,
#         {
#             "asset_assignments": asset_assignments,
#             "filter_dict": data_dict,
#             "field": field,
#             "pd": previous_data,
#             "requests_ids": requests_ids,
#         },
#     )
