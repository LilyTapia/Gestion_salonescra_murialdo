from django.db import migrations, models

SUBJECTS_BY_LEVEL = {
    'BASICO': [
        'Ciencias',
        'Matemáticas',
        'Educación Física',
        'Lenguaje',
        'Inglés',
        'Artes',
        'Tecnología',
        'Música',
        'Religión',
        'Historia',
        'Orientación',
    ],
    'MEDIO_1_2': [
        'Inglés',
        'Tutoría',
        'Matemáticas',
        'Educación Física',
        'Lenguaje',
        'Biología',
        'Historia',
        'Física',
        'Química',
        'Artes',
        'Tecnología',
        'Religión',
        'Orientación',
    ],
    'MEDIO_3_4': [
        'Tutoría',
        'Lenguaje',
        'Inglés',
        'Matemáticas',
        'Módulo Geo3D',
        'Taller Historia',
        'Ciencias para la Ciudadanía',
        'Módulo CompHist',
        'Módulo InterpMus',
        'TAF',
        'Filosofía',
    ],
}

SUBJECT_NORMALIZATION = {
    'Matematicas': 'Matemáticas',
    'Educacion Fisica': 'Educación Física',
    'Ingles': 'Inglés',
    'Tecnologia': 'Tecnología',
    'Musica': 'Música',
    'Religion': 'Religión',
    'Orientacion': 'Orientación',
    'Tutoria': 'Tutoría',
    'Fisica': 'Física',
    'Quimica': 'Química',
}


def apply_course_levels(apps, schema_editor):
    Course = apps.get_model('booking', 'Course')
    for course in Course.objects.all():
        name = course.name.lower()
        if 'medio' in name:
            if name.strip().startswith(('1°', '2°')):
                course.level_group = 'MEDIO_1_2'
            else:
                course.level_group = 'MEDIO_3_4'
        else:
            course.level_group = 'BASICO'
        course.save(update_fields=['level_group'])


def update_subjects_and_roles(apps, schema_editor):
    Subject = apps.get_model('booking', 'Subject')
    TeacherRole = apps.get_model('booking', 'TeacherRole')

    for old, new in SUBJECT_NORMALIZATION.items():
        try:
            subject = Subject.objects.get(name=old)
        except Subject.DoesNotExist:
            continue
        if subject.name != new:
            subject.name = new
            subject.save(update_fields=['name'])

    all_names = []
    for names in SUBJECTS_BY_LEVEL.values():
        all_names.extend(names)

    for name in dict.fromkeys(all_names):
        Subject.objects.get_or_create(name=name)

    TeacherRole.objects.get_or_create(name='Docente')


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_teacherprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='level_group',
            field=models.CharField(
                choices=[
                    ('BASICO', '1° a 8° Basico'),
                    ('MEDIO_1_2', '1° y 2° Medio'),
                    ('MEDIO_3_4', '3° y 4° Medio'),
                ],
                default='BASICO',
                max_length=20,
            ),
        ),
        migrations.RunPython(update_subjects_and_roles, migrations.RunPython.noop),
        migrations.RunPython(apply_course_levels, migrations.RunPython.noop),
    ]
