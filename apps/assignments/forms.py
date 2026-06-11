from django import forms

from apps.assignments.models import Task
from apps.core.models import Teacher


class TaskCreateForm(forms.ModelForm):

    class Meta:

        model = Task

        fields = (
            'title',
            'description',
            'teacher',
            'due_date',
            'priority',
            'attachment',
        )

        labels = {
            'title': 'Название',
            'description': 'Описание',
            'teacher': 'Преподаватель',
            'due_date': 'Срок выполнения',
            'priority': 'Приоритет',
            'attachment': 'Вложение',
        }

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5
                }
            ),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.ClearableFileInput(
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['teacher'].queryset = Teacher.objects.select_related(
            'user'
        ).order_by('full_name')


class TaskUpdateForm(TaskCreateForm):

    class Meta(TaskCreateForm.Meta):

        fields = TaskCreateForm.Meta.fields + (
            'status',
        )

        labels = {
            **TaskCreateForm.Meta.labels,
            'status': 'Статус',
        }

        widgets = {
            **TaskCreateForm.Meta.widgets,
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
