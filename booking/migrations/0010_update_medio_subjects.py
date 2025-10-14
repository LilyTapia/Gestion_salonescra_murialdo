from django.db import migrations

NEW_MEDIO_SUBJECTS = [
    # 1° y 2° Medio
    'Lenguaje',
    'Matemáticas',
    'Historia',
    'Biología',
    'Química',
    'Física',
    'Inglés',
    'Tecnología',
    'Artes',
    'Música',
    'Educación Física',
    'Religión',
    'Orientación',
    'Taller de Ciencias',
    'TAF',
    'Taller de competencias socioemocionales',
    'TMMCO',
    'Tutoría',
    # 3° y 4° Medio (módulos 2024)
    'Educación Ciudadana',
    'Ciencias para la Ciudadanía',
    'Taller de Historia',
    'Participación y argumentación en democracia',
    'Comprensión histórica del presente',
    'Geografía, territorio y desafíos socioambientales',
    'Probabilidades y estadísticas',
    'Geometría 3D',
    'Ciencias de la salud',
    'Biología celular y molecular',
    'Ciencias del ejercicio físico y deportivo',
    'Arquitectura y diseño',
    'Interpretación musical',
]


def add_medio_subjects(apps, schema_editor):
    Subject = apps.get_model('booking', 'Subject')
    for name in NEW_MEDIO_SUBJECTS:
        Subject.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_update_basico_subjects'),
    ]

    operations = [
        migrations.RunPython(add_medio_subjects, migrations.RunPython.noop),
    ]
