from django.contrib import admin
from .models import Room, Material, RoomInventory, Reservation, ReservationItem, Blackout, Subject, TeacherRole, Course, TeacherProfile

admin.site.register(Room)
admin.site.register(Material)
admin.site.register(RoomInventory)
admin.site.register(Reservation)
admin.site.register(ReservationItem)
admin.site.register(Blackout)

admin.site.register(Subject)
admin.site.register(TeacherRole)
admin.site.register(Course)
admin.site.register(TeacherProfile)
