from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from booking.dateutils import max_reservation_date
from booking.models import Course, Reservation, Room, Subject
from booking.services import build_registration_metadata

class ReservationTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(code="A")

    def test_create_reservation(self):
        r = Reservation.objects.create(room=self.room, date=date.today(), start_time=time(10,0), end_time=time(11,0))
        self.assertIsNotNone(r.id)


class MaxReservationDateTests(TestCase):
    def test_end_of_month_rolls_back(self):
        base_date = date(2025, 1, 31)
        expected = date(2025, 2, 28)
        self.assertEqual(expected, max_reservation_date(base_date))


class ReservationLimitTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(code="B")
        self.course, _ = Course.objects.get_or_create(name="1 Basico A", defaults={"order": 1})
        self.subject, _ = Subject.objects.get_or_create(name="Matemáticas")
        self.user = User.objects.create_user(username="docente", password="pass1234")
        self.client.login(username="docente", password="pass1234")

    def _build_form_payload(self, *, target_date):
        return {
            "room": self.room.id,
            "date": target_date.isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "course": self.course.id,
            "subject": self.subject.id,
        }

    def test_reservation_create_rejects_beyond_one_month(self):
        today = timezone.localdate()
        limit = max_reservation_date(today)
        beyond = limit + timedelta(days=1)

        response = self.client.post(
            reverse("reservation_create"),
            data=self._build_form_payload(target_date=beyond),
            follow=True,
        )

        self.assertEqual(0, Reservation.objects.count())
        messages = []
        if response.context is not None:
            if isinstance(response.context, list):
                for ctx in response.context:
                    if "messages" in ctx:
                        messages.extend(list(ctx["messages"]))
            else:
                messages.extend(list(response.context["messages"]))
        self.assertTrue(
            any("1 mes" in message.message for message in messages),
            "Expected validation message about 1 month limit.",
        )

    def test_reservation_create_allows_date_at_limit(self):
        today = timezone.localdate()
        limit = max_reservation_date(today)

        response = self.client.post(
            reverse("reservation_create"),
            data=self._build_form_payload(target_date=limit),
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual(1, Reservation.objects.count())

    def test_reservation_api_rejects_beyond_one_month(self):
        today = timezone.localdate()
        limit = max_reservation_date(today)
        beyond = limit + timedelta(days=1)

        api_client = APIClient()
        api_client.force_authenticate(self.user)
        payload = {
            "room": self.room.id,
            "date": beyond.isoformat(),
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "items": [],
        }

        response = api_client.post("/api/reservations/", payload, format="json")

        self.assertEqual(400, response.status_code)
        self.assertIn("1 mes", str(response.data))


class RegistrationMetadataTests(TestCase):
    def test_basic_subjects_include_curriculum_updates(self):
        metadata = build_registration_metadata()
        basico_subjects = metadata["subjects_by_level"].get("BASICO", [])
        subject_names = {entry["name"] for entry in basico_subjects}
        expected_basico = {
            "Lengua y cultura de pueblos originarios",
            "Taller de competencias socioemocionales",
            "Taller de inglés",
            "Taller de tecnología",
            "Taller de lectoescritura",
            "Taller de acondicionamiento físico",
            "Taller de artes",
            "Taller de música",
            "TMMCO",
        }
        for name in expected_basico:
            self.assertIn(name, subject_names)

    def test_medio_subjects_include_curriculum_updates(self):
        metadata = build_registration_metadata()
        medio_1_2_names = {entry["name"] for entry in metadata["subjects_by_level"].get("MEDIO_1_2", [])}
        medio_3_4_names = {entry["name"] for entry in metadata["subjects_by_level"].get("MEDIO_3_4", [])}

        expected_medio_1_2 = {
            "Taller de Ciencias",
            "TAF",
            "TMMCO",
            "Taller de competencias socioemocionales",
        }
        expected_medio_3_4 = {
            "Participación y argumentación en democracia",
            "Comprensión histórica del presente",
            "Geografía, territorio y desafíos socioambientales",
            "Probabilidades y estadísticas",
            "Geometría 3D",
            "Ciencias de la salud",
            "Biología celular y molecular",
            "Ciencias del ejercicio físico y deportivo",
            "Arquitectura y diseño",
            "Interpretación musical",
        }

        for name in expected_medio_1_2:
            self.assertIn(name, medio_1_2_names)
        for name in expected_medio_3_4:
            self.assertIn(name, medio_3_4_names)


class RegistrationEmailValidationTests(TestCase):
    def test_register_rejects_non_murialdo_email(self):
        payload = {
            "username": "prof_nope",
            "first_name": "Ana",
            "last_name": "Docente",
            "email": "ana@example.com",
            "password1": "AdminPass123",
            "password2": "AdminPass123",
        }
        response = self.client.post(reverse("register"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="prof_nope").exists())

    def test_register_accepts_murialdo_email(self):
        payload = {
            "username": "prof_ok",
            "first_name": "Luis",
            "last_name": "Murialdo",
            "email": "luis@murialdovalpo.cl",
            "password1": "AdminPass123",
            "password2": "AdminPass123",
        }
        response = self.client.post(reverse("register"), payload)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="prof_ok").exists())
