from django import forms
from django.contrib.auth.models import User

from .models import (
    Comment,
    Milestone,
    Project,
    ProjectMembership,
    Task,
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "visibility",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your project name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe what your project is about",
                    "rows": 5,
                }
            ),
            "visibility": forms.Select(),
        }


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = [
            "title",
            "description",
            "due_date",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter milestone title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe this milestone",
                    "rows": 4,
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "milestone",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
        ]

        widgets = {
            "milestone": forms.Select(),
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter task title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe this task",
                    "rows": 5,
                }
            ),
            "status": forms.Select(),
            "priority": forms.Select(),
            "assignee": forms.Select(),
        }

    def __init__(
        self,
        *args,
        project=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        milestone_field = self.fields["milestone"]
        assignee_field = self.fields["assignee"]

        assert isinstance(
            milestone_field,
            forms.ModelChoiceField,
        )

        assert isinstance(
            assignee_field,
            forms.ModelChoiceField,
        )

        milestone_field.required = False
        assignee_field.required = False

        if project is None:
            milestone_field.queryset = Milestone.objects.none()
            assignee_field.queryset = User.objects.none()

            milestone_field.empty_label = "No milestone"
            assignee_field.empty_label = "Unassigned"

            return

        milestone_field.queryset = Milestone.objects.filter(
            project=project,
        )

        milestone_field.empty_label = "No milestone"

        member_ids = ProjectMembership.objects.filter(
            project=project,
        ).values_list(
            "user_id",
            flat=True,
        )

        assignee_field.queryset = User.objects.filter(
            id__in=member_ids,
        )

        assignee_field.empty_label = "Unassigned"


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = [
            "body",
        ]

        widgets = {
            "body": forms.Textarea(
                attrs={
                    "placeholder": "Write a comment...",
                    "rows": 4,
                }
            ),
        }


class MemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        empty_label="Select a user",
    )

    def __init__(
        self,
        *args,
        project=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        user_field = self.fields["user"]

        assert isinstance(
            user_field,
            forms.ModelChoiceField,
        )

        if project is None:
            return

        existing_member_ids = (
            ProjectMembership.objects.filter(
                project=project,
            )
            .values_list(
                "user_id",
                flat=True,
            )
        )

        user_field.queryset = User.objects.exclude(
            id__in=existing_member_ids,
        )
