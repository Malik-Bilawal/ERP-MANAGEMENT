from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'time-entries', views.TimeEntryViewSet)
router.register(r'milestones', views.MilestoneViewSet)
router.register(r'documents', views.ClientDocumentViewSet)
router.register(r'communications', views.ClientCommunicationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]