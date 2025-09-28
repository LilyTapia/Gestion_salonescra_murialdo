from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_update_teacher_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservations', to='booking.course'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservations', to='booking.subject'),
        ),
    ]
