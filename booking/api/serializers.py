import datetime as _dt
from django.db import transaction, models
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from booking.models import Room, Material, RoomInventory, Reservation, ReservationItem, Blackout

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
        request = self.context.get("request")
        is_admin_user = False
        if request and request.user.is_authenticated:
            is_admin_user = request.user.is_staff or request.user.groups.filter(name='AdminBiblioteca').exists()
        if date and not is_admin_user:
            max_allowed = today + _dt.timedelta(days=30)
            if date > max_allowed:
                raise serializers.ValidationError("Las reservas solo se permiten hasta con 30 dias de anticipacion.")
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
        with transaction.atomic():
            r = Reservation.objects.create(user=(request.user if request and request.user.is_authenticated else None), **validated_data)
            for it in items_data:
                material = it["material"]; qty = it["quantity"]
                inv = RoomInventory.objects.select_for_update().get(room=room, material=material)
                if inv.quantity < qty:
                    raise serializers.ValidationError(f"Sin stock suficiente de {material.name} en salón {room.code}.")
                inv.quantity -= qty; inv.save()
                ReservationItem.objects.create(reservation=r, material=material, quantity=qty)
        return r

    def _apply_stock_delta(self, room, deltas):
        for material, delta in deltas.items():
            inv = RoomInventory.objects.select_for_update().get(room=room, material=material)
            new_qty = inv.quantity - delta  # delta positivo = consumir más; negativo = devolver
            if new_qty < 0:
                raise serializers.ValidationError(f"Stock insuficiente de {material.name} en salón {room.code}.")
            inv.quantity = new_qty; inv.save()

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
                old_map = {it.material: it.quantity for it in instance.items.all()}
                new_map = {}
                for it in new_items:
                    m = it["material"]; q = it["quantity"]
                    new_map[m] = new_map.get(m,0) + q
                deltas = {}
                for m in set(old_map)|set(new_map):
                    deltas[m] = new_map.get(m,0) - old_map.get(m,0)
                self._apply_stock_delta(new_room, deltas)
                instance.items.all().delete()
                for m,q in new_map.items():
                    ReservationItem.objects.create(reservation=instance, material=m, quantity=q)
            for k,v in validated_data.items():
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
