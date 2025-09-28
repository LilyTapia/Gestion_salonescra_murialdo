from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from datetime import datetime, date as date_cls, timedelta
from django.utils import timezone
import calendar
import json
from .models import Room, Material, Reservation, Blackout, RoomInventory, Subject, TeacherRole, Course, TeacherProfile

BASIC_SUBJECT_NAMES = [
    'Ciencias', 'Matematicas', 'Educacion Fisica', 'Lenguaje', 'Ingles',
    'Artes', 'Tecnologia', 'Musica', 'Religion', 'Historia', 'Orientacion'
]

MEDIO_1_2_SUBJECT_NAMES = [
    'Ingles', 'Tutoria', 'Matematicas', 'Educacion Fisica', 'Lenguaje', 'Biologia',
    'Historia', 'Fisica', 'Quimica', 'Artes', 'Tecnologia', 'Religion', 'Orientacion'
]

MEDIO_3_4_SUBJECT_NAMES = [
    'Tutoria', 'Lenguaje', 'Ingles', 'Matematicas', 'Modulo Geo3D', 'Taller Historia',
    'Ciencias para la ciudadania', 'Modulo CompHist', 'Modulo InterpMus', 'TAF', 'Filosofia'
]

def _course_stage(course_name):
    try:
        parts = course_name.split()
        level = int(parts[0])
        stage = parts[1].lower()
        if stage == 'basico':
            return 'basico'
        if stage == 'medio':
            return 'medio12' if level <= 2 else 'medio34'
    except (ValueError, IndexError):
        pass
    return 'basico'

class ReservationForm(forms.Form):
    room = forms.ModelChoiceField(
        queryset=Room.objects.all(),
        label='Salón',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha'
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Inicio'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Término'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        required=True,
        label='Curso',
        help_text='Selecciona el curso que asistirá al salón.',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        required=True,
        label='Asignatura',
        help_text='Selecciona la asignatura que se dictará en el salón.',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, user=None, **kwargs):
        self.request_user = user
        super().__init__(*args, **kwargs)

        courses_qs = Course.objects.order_by('order', 'name')
        subjects_qs = Subject.objects.order_by('name')

        profile = None
        if user and hasattr(user, 'teacher_profile'):
            profile = user.teacher_profile

        if profile:
            profile_courses = profile.courses.order_by('order', 'name')
            profile_subjects = profile.subjects.order_by('name')
            if profile_courses.exists():
                courses_qs = profile_courses
            if profile_subjects.exists():
                subjects_qs = profile_subjects

        self.fields['course'].queryset = courses_qs
        self.fields['subject'].queryset = subjects_qs
        self.fields['course'].empty_label = 'Selecciona un curso'
        self.fields['subject'].empty_label = 'Selecciona una asignatura'

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError('La hora de inicio debe ser menor que la de término.')
        return cleaned


class BlackoutForm(forms.ModelForm):
    date = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={"type": "date"})
    )
    start_time = forms.TimeField(
        label="Inicio",
        widget=forms.TimeInput(attrs={"type": "time", "readonly": "readonly"})
    )
    end_time = forms.TimeField(
        label="Termino",
        widget=forms.TimeInput(attrs={"type": "time", "readonly": "readonly"})
    )
    repeat = forms.ChoiceField(
        label="Repeticion",
        choices=[
            ("none", "Sin repeticion"),
            ("weekly", "Semana completa"),
            ("monthly", "Mensual"),
        ],
        initial="none"
    )
    repeat_until = forms.DateField(
        label="Repetir hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Requerido si seleccionas un bloqueo mensual."
    )

    class Meta:
        model = Blackout
        fields = ["room", "reason"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._occurrences = []

        if self.instance and self.instance.pk:
            start_dt = self.instance.start_datetime
            end_dt = self.instance.end_datetime
            self.fields["date"].initial = start_dt.date()
            self.fields["start_time"].initial = start_dt.time()
            self.fields["end_time"].initial = end_dt.time()
            # Repeat options only for existing records
            self.fields["repeat"].initial = "none"
            self.fields["repeat"].widget = forms.HiddenInput()
            self.fields["repeat_until"].widget = forms.HiddenInput()
        else:
            # Pre-fill with today when creating a new blackout
            self.fields["date"].initial = datetime.today().date()

    def clean(self):
        cleaned = super().clean()
        date_value = cleaned.get("date")
        start_time = cleaned.get("start_time")
        end_time = cleaned.get("end_time")
        repeat = cleaned.get("repeat") or "none"
        repeat_until = cleaned.get("repeat_until")

        if date_value and start_time and end_time:
            today = timezone.localdate()
            if date_value < today:
                self.add_error("date", "La fecha del bloqueo debe ser igual o posterior a hoy.")
                return cleaned

            start_dt = datetime.combine(date_value, start_time)
            end_dt = datetime.combine(date_value, end_time)

            if start_dt >= end_dt:
                self.add_error("end_time", "La hora de termino debe ser mayor que la hora de inicio.")
            else:
                occurrences = [(start_dt, end_dt)]

                if repeat == "weekly":
                    for offset in range(1, 7):
                        next_date = date_value + timedelta(days=offset)
                        occurrences.append((
                            datetime.combine(next_date, start_time),
                            datetime.combine(next_date, end_time)
                        ))
                elif repeat == "monthly":
                    if not repeat_until:
                        self.add_error("repeat_until", "Debes indicar una fecha limite para la repeticion.")
                    elif repeat_until < date_value:
                        self.add_error("repeat_until", "La fecha limite debe ser posterior a la fecha inicial.")
                    else:
                        current_date = date_value
                        while True:
                            current_date = self._add_one_month(current_date)

                            if current_date is None or current_date > repeat_until:
                                break

                            occurrences.append(
                                (
                                    datetime.combine(current_date, start_time),
                                    datetime.combine(current_date, end_time)
                                )
                            )

                self._occurrences = occurrences
                cleaned["start_datetime"] = occurrences[0][0]
                cleaned["end_datetime"] = occurrences[0][1]
        return cleaned

    def _add_one_month(self, base_date: date_cls):
        """Return the same day next month, adjusting to the last valid day if needed."""
        year = base_date.year
        month = base_date.month + 1
        if month > 12:
            month = 1
            year += 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(base_date.day, last_day)
        try:
            return date_cls(year, month, day)
        except ValueError:
            return None

    def get_occurrences(self):
        return list(self._occurrences or [])

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del material"})
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Requerido. Ingresa una direccion de email valida.')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellidos')
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
        label='Asignaturas que imparte',
        help_text='Selecciona una o varias asignaturas (mantén presionada la tecla Ctrl o Cmd para múltiples).'
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=TeacherRole.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label='Cargos',
        help_text='Selecciona todos los cargos que correspondan.'
    )
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
        label='Cursos a cargo',
        help_text='Selecciona uno o varios cursos (mantén presionada la tecla Ctrl o Cmd para múltiples).'
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2", "subjects", "roles", "courses")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subjects'].queryset = Subject.objects.order_by('name')
        self.fields['roles'].queryset = TeacherRole.objects.order_by('name')
        self.fields['courses'].queryset = Course.objects.order_by('order', 'name')

    def _save_profile_data(self, user):
        profile, _ = TeacherProfile.objects.get_or_create(user=user)
        subjects = self.cleaned_data.get('subjects') or []
        roles = self.cleaned_data.get('roles') or []
        courses = self.cleaned_data.get('courses') or []
        profile.subjects.set(subjects)
        profile.roles.set(roles)
        profile.courses.set(courses)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = True
        if commit:
            user.save()
            docente_group, _ = Group.objects.get_or_create(name='Docente')
            user.groups.add(docente_group)
            self._save_profile_data(user)
        return user


class InventoryForm(forms.ModelForm):
    class Meta:
        model = RoomInventory
        fields = ["room", "material", "quantity"]
        widgets = {
            "room": forms.Select(attrs={"class": "form-control"}),
            "material": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"})
        }

class InventoryUpdateForm(forms.Form):
    action = forms.ChoiceField(
        choices=[("add", "Agregar"), ("remove", "Quitar"), ("set", "Establecer")],
        widget=forms.Select(attrs={"class": "form-control"})
    )
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"})
    )


class AdminUserCreationForm(forms.ModelForm):
    """Formulario completo para crear usuarios desde el panel de administracion"""
    password1 = forms.CharField(
        label='Contrasena',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar contrasena',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Grupos'
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
        label='Asignaturas que imparte'
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=TeacherRole.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label='Cargos'
    )
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
        label='Cursos a cargo'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subjects'].queryset = Subject.objects.order_by('name')
        self.fields['roles'].queryset = TeacherRole.objects.order_by('name')
        self.fields['courses'].queryset = Course.objects.order_by('order', 'name')
        if self.instance and self.instance.pk:
            profile = getattr(self.instance, 'teacher_profile', None)
            if profile:
                self.fields['subjects'].initial = profile.subjects.all()
                self.fields['roles'].initial = profile.roles.all()
                self.fields['courses'].initial = profile.courses.all()

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contrasenas no coinciden.')
        return password2

    def _save_profile_data(self, user):
        profile, _ = TeacherProfile.objects.get_or_create(user=user)
        subjects = self.cleaned_data.get('subjects') or []
        roles = self.cleaned_data.get('roles') or []
        courses = self.cleaned_data.get('courses') or []
        profile.subjects.set(subjects)
        profile.roles.set(roles)
        profile.courses.set(courses)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        if commit:
            user.save()
            groups = self.cleaned_data.get('groups')
            if groups:
                user.groups.set(groups)
            self._save_profile_data(user)
        return user



