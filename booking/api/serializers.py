import datetime as _dt
from django.db import transaction, models
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from booking.models import Room, Material, RoomInventory, Reservation, ReservationItem, Blackout
from booking.services import get_reserved_material_quantity
from booking.dateutils import max_reservation_date

User = get_user_model()

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id","code"]

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id","name"]

class RoomInventorySerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    material = MaterialSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), source="room", write_only=True)
    material_id = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), source="material", write_only=True)
    class Meta:
        model = RoomInventory
        fields = ["id","room","material","quantity","room_id","material_id"]

class ReservationItemSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), source="material", write_only=True)
    class Meta:
        model = ReservationItem
        fields = ["id","material","material_id","quantity"]

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","email"]

def _dt_join(d, t):
    return _dt.datetime.combine(d, t)

class ReservationSerializer(serializers.ModelSerializer):
    items = ReservationItemSerializer(many=True)
    user = UserMiniSerializer(read_only=True)
    inventory_released = serializers.BooleanField(read_only=True)
    class Meta:
        model = Reservation
        fields = ["id","room","date","start_time","end_time","items","inventory_released","user"]
        read_only_fields = ["inventory_released","user"]

    def validate(self, attrs):
        room = attrs.get("room", getattr(self.instance, "room", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        today = timezone.localdate()
        if date and date < today:
            raise serializers.ValidationError("La fecha de la reserva debe ser igual o posterior a hoy.")
        if date:
            max_allowed = max_reservation_date(today)
            if date > max_allowed:
                raise serializers.ValidationError("Las reservas solo se permiten hasta con 1 mes de anticipacion.")
        if start and end and start >= end:
            raise serializers.ValidationError("La hora de inicio debe ser menor que la de término.")
        # L-V 08:00–18:00
        if date and (date.weekday() > 4):
            raise serializers.ValidationError("Solo se permiten reservas de lunes a viernes.")
        if start and end:
            if not (_dt.time(8,0) <= start < _dt.time(18,0) and _dt.time(8,0) < end <= _dt.time(18,0)):
                raise serializers.ValidationError("Horario permitido: 08:00 a 18:00.")
        # Choque con reservas existentes
        qs = Reservation.objects.filter(room=room, date=date, start_time__lt=end, end_time__gt=start)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("El salón ya está ocupado en ese horario.")
        # Choque con blackouts (global o por salón)
        start_dt = _dt_join(date, start); end_dt = _dt_join(date, end)
        blackout_exists = Blackout.objects.filter(
            models.Q(room__isnull=True) | models.Q(room=room),
            start_datetime__lt=end_dt,
            end_datetime__gt=start_dt
        ).exists()
        if blackout_exists:
            raise serializers.ValidationError("Existe un bloqueo de agenda en ese horario (feriado/reunión).")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        items_data = validated_data.pop("items", [])
        room = validated_data["room"]
        date = validated_data["date"]
        start = validated_data["start_time"]
        end = validated_data["end_time"]
        material_map = self._aggregate_items(items_data)
        with transaction.atomic():
            self._validate_materials_for_slot(
                room=room,
                date=date,
                start=start,
                end=end,
                material_quantities=material_map,
            )
            reservation = Reservation.objects.create(
                user=(request.user if request and request.user.is_authenticated else None),
                **validated_data
            )
            for material, qty in material_map.items():
                ReservationItem.objects.create(reservation=reservation, material=material, quantity=qty)
        return reservation

    def _aggregate_items(self, items_data):
        material_map = {}
        for item in items_data:
            material = item["material"]
            material_map[material] = material_map.get(material, 0) + item["quantity"]
        return material_map

    def _validate_materials_for_slot(self, *, room, date, start, end, material_quantities, exclude_reservation_id=None):
        for material, qty in material_quantities.items():
            try:
                inventory = RoomInventory.objects.select_for_update().get(room=room, material=material)
            except RoomInventory.DoesNotExist:
                raise serializers.ValidationError(f"No hay inventario configurado para {material.name} en salón {room.code}.")
            reserved_overlap = get_reserved_material_quantity(
                room=room,
                material_id=material.id,
                date=date,
                start_time=start,
                end_time=end,
                exclude_reservation_id=exclude_reservation_id,
            )
            if reserved_overlap + qty > inventory.quantity:
                raise serializers.ValidationError(f"Sin stock suficiente de {material.name} en salón {room.code}.")

    def update(self, instance, validated_data):
        new_items = validated_data.pop("items", None)
        new_room = validated_data.get("room", instance.room)
        new_date = validated_data.get("date", instance.date)
        new_start = validated_data.get("start_time", instance.start_time)
        new_end = validated_data.get("end_time", instance.end_time)
        exists = Reservation.objects.filter(room=new_room, date=new_date, start_time__lt=new_end, end_time__gt=new_start).exclude(pk=instance.pk).exists()
        if exists:
            raise serializers.ValidationError("El salón ya está ocupado en ese horario.")
        with transaction.atomic():
            if new_items is not None:
                material_map = self._aggregate_items(new_items)
            else:
                material_map = {}
                for item in instance.items.all():
                    material_map[item.material] = material_map.get(item.material, 0) + item.quantity
            self._validate_materials_for_slot(
                room=new_room,
                date=new_date,
                start=new_start,
                end=new_end,
                material_quantities=material_map,
                exclude_reservation_id=instance.pk,
            )
            if new_items is not None:
                instance.items.all().delete()
                for material, qty in material_map.items():
                    ReservationItem.objects.create(reservation=instance, material=material, quantity=qty)
            for k, v in validated_data.items():
                setattr(instance, k, v)
            instance.save()
        return instance

class BlackoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blackout
        fields = ["id","room","start_datetime","end_datetime","reason","created_by","created_at"]
        read_only_fields = ["created_by","created_at"]

    def validate(self, attrs):
        if attrs["start_datetime"] >= attrs["end_datetime"]:
            raise serializers.ValidationError("Fecha/hora inicial debe ser menor que la final.")
        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        validated_data["created_by"] = user if user.is_authenticated else None
        return super().create(validated_data)
