from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, ask, health

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = [
    path("health/", health, name="health"),
    path("ask/", ask, name="ask"),
    path("", include(router.urls)),
]
