from django.db import models
from django.utils import timezone
from django.conf import settings

class Room(models.Model):
    code = models.CharField(max_length=1, unique=True)  # 'A', 'B', 'C'
    def __str__(self): return self.code

class Material(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.name

class RoomInventory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ("room","material")

class Reservation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    course = models.ForeignKey('Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservations')
    subject = models.ForeignKey('Subject', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservations')
    created_at = models.DateTimeField(default=timezone.now)
    inventory_released = models.BooleanField(default=False)

    def __str__(self):
        return f"Reserva {self.room.code} {self.date} {self.start_time}-{self.end_time}"

    def release_inventory(self, *, items=None):
        """Return reserved materials to the room's inventory if not yet released."""
        if self.inventory_released:
            return False

        self.inventory_released = True
        self.save(update_fields=['inventory_released'])

        return True

class ReservationItem(models.Model):
    reservation = models.ForeignKey(Reservation, related_name="items", on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

class Blackout(models.Model):
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["room","start_datetime","end_datetime"])]

    HOLIDAY_PREFIX = "feriado"

    @property
    def is_holiday(self):
        reason = (self.reason or "").strip().lower()
        return reason.startswith(self.HOLIDAY_PREFIX)

    @property
    def style_variant(self):
        if self.room_id:
            return "room"
        return "holiday" if self.is_holiday else "general"

    @property
    def display_scope(self):
        if self.room_id:
            return f"Salón {self.room.code}"
        return "Feriado" if self.style_variant == "holiday" else "Bloqueo general"

    @property
    def display_type(self):
        labels = {"room": "Salón", "holiday": "Feriado", "general": "Bloqueo general"}
        return labels[self.style_variant]

    def __str__(self):
        return f"{self.display_scope}: {self.start_datetime}-{self.end_datetime} ({self.reason})"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user} - {self.created_at:%Y-%m-%d %H:%M}"

    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])



class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TeacherRole(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    class LevelGroup(models.TextChoices):
        BASICO = 'BASICO', '1 a 8 Basico'
        MEDIO_1_2 = 'MEDIO_1_2', '1 y 2 Medio'
        MEDIO_3_4 = 'MEDIO_3_4', '3 y 4 Medio'

    name = models.CharField(max_length=20, unique=True)
    order = models.PositiveIntegerField(default=0)
    level_group = models.CharField(
        max_length=20,
        choices=LevelGroup.choices,
        default=LevelGroup.BASICO,
    )

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    roles = models.ManyToManyField(TeacherRole, blank=True, related_name='teachers')
    courses = models.ManyToManyField(Course, blank=True, related_name='teachers')

    def __str__(self):
        return f'Perfil docente de {self.user}'
