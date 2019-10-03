from django.urls import path

from . import views, views_deployments

app_name = 'builds'
urlpatterns = [
    path('', view=views.BuildHomeView.as_view(), name='builds_home'),
    path('<int:pk>/', view=views.BuildDetailView.as_view(), name='builds_detail'),
    # AJAX paths
    path('ajax/detail/<int:pk>/', view=views.BuildAjaxDetailView.as_view(), name='ajax_builds_detail'),
    path('ajax/add/', view=views.BuildAjaxCreateView.as_view(), name='ajax_builds_add'),
    path('ajax/edit/<int:pk>/', view=views.BuildAjaxUpdateView.as_view(), name='ajax_builds_update'),
    path('ajax/delete/<int:pk>/', view=views.BuildAjaxDeleteView.as_view(), name='ajax_builds_delete'),
    path('ajax/action/<action_type>/<int:pk>/', view=views.BuildAjaxActionView.as_view(), name='ajax_builds_action'),
    path('ajax/note/<int:pk>/', view=views.BuildNoteAjaxCreateView.as_view(), name='ajax_note_action'),
    path('ajax/photo-upload/<int:pk>/', view=views.BuildPhotoUploadAjaxCreateView.as_view(), name='ajax_photo_upload_action'),
    path('ajax/load-navtree/', views.load_builds_navtree, name='ajax_load_builds_navtree'),
    path('ajax/snapshot/<int:pk>/', view=views.BuildAjaxSnapshotCreateView.as_view(), name='ajax_builds_snapshot'),
    # Deployment paths
    path('ajax/deployment/add/<int:build_pk>/', view=views_deployments.DeploymentAjaxCreateView.as_view(), name='ajax_deployment_add'),
    path('ajax/deployment/action/<action_type>/<int:pk>/<int:build_pk>/', view=views_deployments.DeploymentAjaxActionView.as_view(), name='ajax_deployment_action'),
]
