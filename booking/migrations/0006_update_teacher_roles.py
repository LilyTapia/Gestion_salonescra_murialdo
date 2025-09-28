from django.db import migrations


def add_and_remove_roles(apps, schema_editor):
    TeacherRole = apps.get_model('booking', 'TeacherRole')
    roles_to_remove = ['Profesor/a', 'Jefe/a de Curso', 'Orientador/a']
    TeacherRole.objects.filter(name__in=roles_to_remove).delete()
    TeacherRole.objects.get_or_create(name='Directivos')


def restore_roles(apps, schema_editor):
    TeacherRole = apps.get_model('booking', 'TeacherRole')
    TeacherRole.objects.get_or_create(name='Profesor/a')
    TeacherRole.objects.get_or_create(name='Jefe/a de Curso')
    TeacherRole.objects.get_or_create(name='Orientador/a')
    TeacherRole.objects.filter(name='Directivos').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_course_levels_subjects'),
    ]

    operations = [
        migrations.RunPython(add_and_remove_roles, restore_roles),
    ]
