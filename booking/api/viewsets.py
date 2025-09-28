from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from booking.models import Room, Material, RoomInventory, Reservation, Blackout
from booking.services import release_overdue_reservations
from .serializers import RoomSerializer, MaterialSerializer, RoomInventorySerializer, ReservationSerializer, BlackoutSerializer
from .permissions import IsOwnerOrReadOnly
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all().order_by("code")
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]

class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Material.objects.all().order_by("name")
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]

class RoomInventoryViewSet(viewsets.ModelViewSet):
    queryset = RoomInventory.objects.select_related("room","material").all()
    serializer_class = RoomInventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["room","material"]

    def list(self, request, *args, **kwargs):
        release_overdue_reservations()
        return super().list(request, *args, **kwargs)

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer

    def get_queryset(self):
        """Filter reservations based on user role - teachers see only their own, admins see all"""
        release_overdue_reservations()
        if self.request.user.is_authenticated:
            # Check if user is admin (staff or AdminBiblioteca group)
            if self.request.user.is_staff or self.request.user.groups.filter(name='AdminBiblioteca').exists():
                # Admins can see all reservations
                return Reservation.objects.prefetch_related("items").all()
            else:
                # Teachers (Docente group) and other users see only their own reservations
                return Reservation.objects.filter(user=self.request.user).prefetch_related("items").all()
        else:
            # Anonymous users see no reservations for list/retrieve, but can still create
            if self.action in ["list", "retrieve"]:
                return Reservation.objects.none()
            return Reservation.objects.prefetch_related("items").all()

    def get_permissions(self):
        if self.action in ["list","retrieve"]:
            return [IsAuthenticated()]  # Changed from AllowAny to IsAuthenticated
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"room":["exact"], "date":["exact","gte","lte","range"]}
    ordering_fields = ["date","start_time","end_time"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance.release_inventory(items=instance.items.select_related("material"))
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BlackoutViewSet(viewsets.ModelViewSet):
    # Only show administrative blackouts, not reservation-generated ones
    queryset = Blackout.objects.select_related("room").exclude(
        reason__startswith='Reserva de'
    ).all()
    serializer_class = BlackoutSerializer
    permission_classes = [IsAdminUser]
