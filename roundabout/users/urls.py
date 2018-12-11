from django.urls import path

from . import views
from roundabout.users.views import (
    user_list_view,
    user_redirect_view,
    user_update_view,
    user_detail_view,
)

app_name = "users"
urlpatterns = [
    path('admin/<int:pk>/', view=views.UserAdminDetailView.as_view(), name='user_admin_detail'),
    path('admin/add/', view=views.UserAdminCreateView.as_view(), name='user_admin_add'),
    path('admin/edit/<int:pk>/', view=views.UserAdminUpdateView.as_view(), name='user_admin_update'),
    path('admin/edit/password/<int:pk>/', view=views.UserAdminPasswordChangeView.as_view(), name='user_admin_change_password'),
    path('admin/delete/<int:pk>/', view=views.UserAdminDeleteView.as_view(), name='user_admin_delete'),
    # Base User paths from Allauth
    path("", view=user_list_view, name="list"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
