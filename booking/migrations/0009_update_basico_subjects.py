from django.db import migrations

NEW_BASICO_SUBJECTS = [
    'Lenguaje',
    'Lengua y cultura de pueblos originarios',
    'Matemáticas',
    'Historia',
    'Ciencias',
    'Inglés',
    'Artes',
    'Tecnología',
    'Música',
    'Educación Física',
    'Religión',
    'Orientación',
    'TMMCO',
    'Tutoría',
    'Taller de competencias socioemocionales',
    'Taller de acondicionamiento físico',
    'Taller de artes',
    'Taller de música',
    'Taller de inglés',
    'Taller de tecnología',
    'Taller de lectoescritura',
]


def add_basico_subjects(apps, schema_editor):
    Subject = apps.get_model('booking', 'Subject')
    for name in NEW_BASICO_SUBJECTS:
        Subject.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_normalize_inventory'),
    ]

    operations = [
        migrations.RunPython(add_basico_subjects, migrations.RunPython.noop),
    ]
