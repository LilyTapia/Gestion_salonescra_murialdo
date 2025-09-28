from django.test import TestCase
from datetime import date, time
from booking.models import Room, Reservation

class ReservationTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(code="A")

    def test_create_reservation(self):
        r = Reservation.objects.create(room=self.room, date=date.today(), start_time=time(10,0), end_time=time(11,0))
        self.assertIsNotNone(r.id)
