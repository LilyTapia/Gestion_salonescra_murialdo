from django.db import models
from django.utils import timezone
from django.db.models import Sum

from .models import Reservation, ReservationItem, Course, Subject, TeacherRole
from .constants import SUBJECTS_BY_LEVEL


def release_overdue_reservations(now=None):
    """Release inventory for reservations that have already finished."""
    current_dt = timezone.localtime(now) if now else timezone.localtime()
    current_date = current_dt.date()
    current_time = current_dt.time()

    overdue_reservations = (
        Reservation.objects.select_related('room')
        .prefetch_related('items__material')
        .filter(inventory_released=False)
        .filter(
            models.Q(date__lt=current_date)
            | (models.Q(date=current_date) & models.Q(end_time__lte=current_time))
        )
    )

    released = 0
    for reservation in overdue_reservations:
        if reservation.release_inventory(items=reservation.items.all()):
            released += 1

    return released


def get_reserved_material_quantity(*, room, material_id, date, start_time, end_time, exclude_reservation_id=None):
    """Return total quantity of a material already reserved for the same slot."""
    overlap_qs = ReservationItem.objects.filter(
        reservation__room=room,
        material_id=material_id,
        reservation__date=date,
        reservation__start_time__lt=end_time,
        reservation__end_time__gt=start_time,
    )
    if exclude_reservation_id:
        overlap_qs = overlap_qs.exclude(reservation_id=exclude_reservation_id)
    return overlap_qs.aggregate(total=Sum('quantity'))['total'] or 0



ACADEMIC_ROLE_NAMES = ('Docente', 'Coordinador/a')


def build_registration_metadata():
    """Return course-level and subject metadata for dynamic registration forms."""
    courses = Course.objects.order_by('order', 'name')
    course_levels = {course.id: course.level_group for course in courses}

    all_subject_names = []
    for names in SUBJECTS_BY_LEVEL.values():
        all_subject_names.extend(names)

    subject_map = {}
    for subject in Subject.objects.filter(name__in=all_subject_names).order_by('name'):
        subject_map.setdefault(subject.name, {'id': subject.id, 'name': subject.name})

    subjects_by_level = {}
    for level, names in SUBJECTS_BY_LEVEL.items():
        subjects_by_level[level] = [subject_map[name] for name in names if name in subject_map]

    academic_role_ids = list(
        TeacherRole.objects.filter(name__in=ACADEMIC_ROLE_NAMES).values_list('id', flat=True)
    )

    return {
        'course_levels': course_levels,
        'subjects_by_level': subjects_by_level,
        'academic_role_ids': academic_role_ids,
    }
