from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .viewsets import RoomViewSet, MaterialViewSet, RoomInventoryViewSet, ReservationViewSet, BlackoutViewSet

router = DefaultRouter()
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"materials", MaterialViewSet, basename="material")
router.register(r"inventory", RoomInventoryViewSet, basename="inventory")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"blackouts", BlackoutViewSet, basename="blackout")

urlpatterns = [
    path("", include(router.urls)),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
