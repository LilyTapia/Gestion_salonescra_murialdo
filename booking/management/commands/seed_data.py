from django.core.management.base import BaseCommand
from booking.models import Room, Material, RoomInventory

# BASE_MATERIALS = ["notebook", "data", "parlantes"]

class Command(BaseCommand):
    help = "Crea salones A/B/C"

    def handle(self, *args, **options):
        rooms = []
        for c in ("A","B","C"):
            r, _ = Room.objects.get_or_create(code=c)
            rooms.append(r)
        # mats = []
        # for name in BASE_MATERIALS:
        #     m, _ = Material.objects.get_or_create(name=name)
        #     mats.append(m)
        # created = 0
        # for r in rooms:
        #     for m in mats:
        #         inv, was_created = RoomInventory.objects.get_or_create(room=r, material=m, defaults={"quantity":5})
        #         if not was_created and inv.quantity == 0:
        #             inv.quantity = 5; inv.save()
        #         created += int(was_created)
        # self.stdout.write(self.style.SUCCESS(f"Seed OK. Inventario creados/norm: {created}"))
        self.stdout.write(self.style.SUCCESS("Seed OK. Salones creados"))
