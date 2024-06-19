"""
assets/sidebar.py
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as trans

MENU = trans("Operations")
IMG_SRC = "images/ui/assets.svg"

SUBMENUS = [
    {
        "menu": trans("Dashboard"),
        "redirect": reverse("operations-dashboard"),
        "accessability": "operations.sidebar.dashboard_accessability",
    },
    {
        "menu": trans("Operations List"),
        "redirect": reverse("operations-list"),
        "accessability": "operations.sidebar.dashboard_accessability",
    },
    # {
    #     "menu": trans("Request and Allocation"),
    #     "redirect": reverse("asset-request-allocation-view"),
    # },
    # {
    #     "menu": trans("Asset History"),
    #     "redirect": reverse("asset-history"),
    # },
]


def dashboard_accessability(request, submenu, user_perms, *args, **kwargs):
    return request.user.has_perm("asset.view_operation")
