from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from booking.models import TeacherProfile

class Command(BaseCommand):
    help = "Crea usuarios de ejemplo: 1 admin y 3 docentes con correos institucionales"

    def handle(self, *args, **options):
        User = get_user_model()
        # Grupos
        admin_group, _ = Group.objects.get_or_create(name="AdminBiblioteca")
        docente_group, _ = Group.objects.get_or_create(name="Docente")

        # Admin
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_user(username="admin", email="admin@colegio.cl", password="admin1234", is_staff=True, is_superuser=True)
            admin.groups.add(admin_group)
            TeacherProfile.objects.get_or_create(user=admin)
            self.stdout.write(self.style.SUCCESS("Admin creado: admin / admin1234"))
        else:
            admin = User.objects.filter(username="admin").first()
            if admin:
                TeacherProfile.objects.get_or_create(user=admin)
            self.stdout.write("Admin ya existe")

        # Docentes (comentado - crear manualmente si es necesario)
        # docentes = [
        #     ("ana", "ana@colegio.cl"),
        #     ("bruno", "bruno@colegio.cl"),
        #     ("carla", "carla@colegio.cl"),
        # ]
        # for u,e in docentes:
        #     if not User.objects.filter(username=u).exists():
        #         user = User.objects.create_user(username=u, email=e, password="docente123")
        #         user.groups.add(docente_group)
        #         self.stdout.write(self.style.SUCCESS(f"Docente creado: {u} / docente123"))
        #     else:
        #         self.stdout.write(f"Docente {u} ya existe")
