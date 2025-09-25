from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from datetime import datetime, timedelta, date as date_cls
import calendar
from .models import Room, Material, Reservation, Blackout, RoomInventory

class ReservationForm(forms.Form):
    room = forms.ModelChoiceField(queryset=Room.objects.all(), label="Salón")
    date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type":"time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type":"time"}))

    def clean(self):
        cleaned = super().clean()
        s = cleaned.get("start_time"); e = cleaned.get("end_time")
        if s and e and s >= e:
            raise forms.ValidationError("La hora de inicio debe ser menor que la de término.")
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
            ("weekly", "Semanal"),
            ("monthly", "Mensual"),
        ],
        initial="none"
    )
    repeat_until = forms.DateField(
        label="Repetir hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Requerido si seleccionas un bloqueo semanal o mensual."
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
            start_dt = datetime.combine(date_value, start_time)
            end_dt = datetime.combine(date_value, end_time)

            if start_dt >= end_dt:
                self.add_error("end_time", "La hora de termino debe ser mayor que la hora de inicio.")
            else:
                occurrences = [(start_dt, end_dt)]

                if repeat in {"weekly", "monthly"}:
                    if not repeat_until:
                        self.add_error("repeat_until", "Debes indicar una fecha limite para la repeticion.")
                    elif repeat_until < date_value:
                        self.add_error("repeat_until", "La fecha limite debe ser posterior a la fecha inicial.")
                    else:
                        current_date = date_value
                        while True:
                            if repeat == "weekly":
                                current_date += timedelta(weeks=1)
                            else:
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
    email = forms.EmailField(required=True, help_text='Requerido. Ingresa una dirección de email válida.')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellidos')

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = True  # Activar automáticamente
        if commit:
            user.save()
            # Asignar automáticamente al grupo Docente
            docente_group, _ = Group.objects.get_or_create(name="Docente")
            user.groups.add(docente_group)
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
    """Formulario completo para crear usuarios desde el panel de administración"""
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Grupos"
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_staff"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True
        if commit:
            user.save()
            # Guardar los grupos seleccionados
            groups = self.cleaned_data.get('groups')
            if groups:
                user.groups.set(groups)
        return user
