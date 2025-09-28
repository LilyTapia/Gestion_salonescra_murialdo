from django.db import models
from django.utils import timezone

from .models import Reservation, Course, Subject, TeacherRole
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
