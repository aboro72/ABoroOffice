from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, LeadViewSet, OpportunityViewSet, ActivityViewSet, NoteViewSet


app_name = 'crm_api'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'accounts', AccountViewSet, basename='accounts')
router.register(r'leads', LeadViewSet, basename='leads')
router.register(r'opportunities', OpportunityViewSet, basename='opportunities')
router.register(r'activities', ActivityViewSet, basename='activities')
router.register(r'notes', NoteViewSet, basename='notes')

urlpatterns = [
    path('', include(router.urls)),
]
