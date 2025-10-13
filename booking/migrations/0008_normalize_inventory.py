from django.db import migrations
from django.db.models import Sum


def normalize_inventory(apps, schema_editor):
    RoomInventory = apps.get_model('booking', 'RoomInventory')
    ReservationItem = apps.get_model('booking', 'ReservationItem')

    outstanding = (
        ReservationItem.objects.filter(reservation__inventory_released=False)
        .values('reservation__room_id', 'material_id')
        .annotate(total=Sum('quantity'))
    )
    outstanding_map = {
        (item['reservation__room_id'], item['material_id']): item['total']
        for item in outstanding
    }

    for inventory in RoomInventory.objects.all():
        delta = outstanding_map.get((inventory.room_id, inventory.material_id))
        if delta:
            inventory.quantity += delta
            inventory.save(update_fields=['quantity'])


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_reservation_course_subject'),
    ]

    operations = [
        migrations.RunPython(normalize_inventory, migrations.RunPython.noop),
    ]
