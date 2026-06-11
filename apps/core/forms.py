from django import forms
from django.core.exceptions import ValidationError

from apps.core.models import StudentGroup
from apps.core.models import Subject
from apps.core.models import Teacher
from apps.core.models import WorkloadPlan
from apps.workload.models import WorkloadAssignment


class WorkloadPlanForm(forms.ModelForm):

    class Meta:

        model = WorkloadPlan

        fields = (
            'кафедра',
            'academic_year',
            'total_hours',
            'status',
        )

        labels = {
            'кафедра': 'Кафедра',
            'academic_year': 'Учебный год',
            'total_hours': 'Общее количество часов',
            'status': 'Статус',
        }

        widgets = {
            'кафедра': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Например: Кафедра информатики'
                }
            ),
            'academic_year': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Например: 2025-2026'
                }
            ),
            'total_hours': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
        }


class TeacherForm(forms.ModelForm):

    class Meta:

        model = Teacher

        fields = (
            'user',
            'full_name',
            'position',
            'academic_degree',
            'rate',
            'max_hours',
        )

        labels = {
            'user': 'Пользователь',
            'full_name': 'ФИО',
            'position': 'Должность',
            'academic_degree': 'Ученая степень',
            'rate': 'Ставка',
            'max_hours': 'Максимальная нагрузка',
        }

        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'academic_degree': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'max_hours': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0
                }
            ),
        }


class SubjectForm(forms.ModelForm):

    class Meta:

        model = Subject

        fields = (
            'name',
            'hours',
            'semester',
            'control_type',
        )

        labels = {
            'name': 'Название',
            'hours': 'Часы',
            'semester': 'Семестр',
            'control_type': 'Тип контроля',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'hours': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0
                }
            ),
            'semester': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1
                }
            ),
            'control_type': forms.Select(attrs={'class': 'form-select'}),
        }


class StudentGroupForm(forms.ModelForm):

    class Meta:

        model = StudentGroup

        fields = (
            'name',
            'course',
            'direction',
        )

        labels = {
            'name': 'Название группы',
            'course': 'Курс',
            'direction': 'Направление',
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1
                }
            ),
            'direction': forms.TextInput(attrs={'class': 'form-control'}),
        }


class WorkloadAssignmentForm(forms.Form):

    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        label='Дисциплина',
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(),
        label='Преподаватель',
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    def __init__(self, *args, **kwargs):

        plan = kwargs.pop('plan')

        super().__init__(*args, **kwargs)

        assigned_subject_ids = WorkloadAssignment.objects.filter(
            plan=plan
        ).values_list(
            'subject_id',
            flat=True
        )

        self.plan = plan

        self.fields['subject'].queryset = Subject.objects.exclude(
            id__in=assigned_subject_ids
        ).order_by('name')

        self.fields['teacher'].queryset = Teacher.objects.select_related(
            'user'
        ).order_by('full_name')


class ImportUploadForm(forms.Form):

    import_type = forms.CharField(
        widget=forms.HiddenInput()
    )

    file = forms.FileField(
        label='Файл XLSX',
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control',
                'accept': '.xlsx'
            }
        )
    )

    plan = forms.ModelChoiceField(
        queryset=WorkloadPlan.objects.none(),
        required=False,
        label='План нагрузки',
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    def __init__(self, *args, **kwargs):

        import_type = kwargs.pop(
            'import_type',
            None
        )

        super().__init__(*args, **kwargs)

        self.fields['plan'].queryset = WorkloadPlan.objects.order_by(
            '-created_at'
        )

        current_import_type = (
            import_type
            or self.initial.get('import_type')
            or self.data.get('import_type')
        )

        if current_import_type:

            self.fields['import_type'].initial = current_import_type

        if current_import_type != 'workload':

            self.fields['plan'].widget = forms.HiddenInput()

            self.fields['plan'].required = False

    def clean_file(self):

        uploaded_file = self.cleaned_data['file']

        if not uploaded_file.name.lower().endswith('.xlsx'):

            raise ValidationError(
                'Поддерживаются только файлы XLSX.'
            )

        return uploaded_file

    def clean(self):

        cleaned_data = super().clean()

        if (
            cleaned_data.get('import_type') == 'workload'
            and cleaned_data.get('plan') is None
        ):

            self.add_error(
                'plan',
                'Для импорта учебного плана нужно выбрать план нагрузки.'
            )

        return cleaned_data
