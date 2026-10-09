from datetime import date, timedelta
from typing import cast

from django import forms
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import MemberForm
from .models import Comment, Milestone, Project, ProjectMembership, Task


class MilestoneCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.create_url = reverse(
            "workspaces:milestone_create",
            kwargs={"slug": self.project.slug},
        )

    def test_logged_out_user_cannot_create_milestone(self):
        response = self.client.get(self.create_url)

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

        self.assertEqual(
            Milestone.objects.count(),
            0,
        )

    def test_project_member_can_open_milestone_form(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(self.create_url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "workspaces/milestone_form.html",
        )

    def test_non_member_cannot_create_milestone(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.get(
            self.create_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        response = self.client.post(
            self.create_url,
            {
                "title": "Unauthorized Milestone",
                "description": "This should not be created.",
                "due_date": "2026-09-30",
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            Milestone.objects.filter(
                title="Unauthorized Milestone",
            ).exists()
        )

    def test_valid_milestone_creation(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        due_date = date.today() + timedelta(days=7)

        response = self.client.post(
            self.create_url,
            {
                "title": "Initial Project Setup",
                "description": (
                    "Set up the ProjectForge foundation."
                ),
                "due_date": due_date.isoformat(),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        milestone = Milestone.objects.get(
            title="Initial Project Setup",
        )

        self.assertEqual(
            milestone.project,
            self.project,
        )

        self.assertEqual(
            milestone.description,
            "Set up the ProjectForge foundation.",
        )

        self.assertEqual(
            milestone.due_date,
            due_date,
        )

    def test_title_is_required(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.create_url,
            {
                "title": "",
                "description": "Milestone without a title.",
                "due_date": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["form"]

        self.assertIn(
            "This field is required.",
            form.errors["title"],
        )

        self.assertEqual(
            Milestone.objects.count(),
            0,
        )

    def test_description_is_optional(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.create_url,
            {
                "title": "Milestone Without Description",
                "description": "",
                "due_date": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        milestone = Milestone.objects.get(
            title="Milestone Without Description",
        )

        self.assertEqual(
            milestone.description,
            "",
        )

    def test_due_date_is_optional(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.create_url,
            {
                "title": "Milestone Without Due Date",
                "description": "No due date is required.",
                "due_date": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        milestone = Milestone.objects.get(
            title="Milestone Without Due Date",
        )

        self.assertIsNone(
            milestone.due_date,
        )

    def test_milestone_is_attached_to_requested_project(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        second_create_url = reverse(
            "workspaces:milestone_create",
            kwargs={
                "slug": second_project.slug,
            },
        )

        response = self.client.post(
            second_create_url,
            {
                "title": "Second Project Milestone",
                "description": "Belongs to the second project.",
                "due_date": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": second_project.slug,
                },
            ),
        )

        milestone = Milestone.objects.get(
            title="Second Project Milestone",
        )

        self.assertEqual(
            milestone.project,
            second_project,
        )

        self.assertNotEqual(
            milestone.project,
            self.project,
        )


class MilestoneEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.milestone = Milestone.objects.create(
            project=self.project,
            title="Initial Project Setup",
            description="Original milestone description.",
            due_date=date(2026, 9, 30),
        )

        self.edit_url = reverse(
            "workspaces:milestone_edit",
            kwargs={
                "slug": self.project.slug,
                "milestone_id": self.milestone.pk,
            },
        )

    def test_project_member_can_open_milestone_edit_form(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(self.edit_url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "workspaces/milestone_form.html",
        )

        self.assertTrue(
            response.context["is_edit"],
        )

        self.assertEqual(
            response.context["milestone"],
            self.milestone,
        )

        self.assertEqual(
            response.context["form"].initial["title"],
            "Initial Project Setup",
        )

        self.assertEqual(
            response.context["form"].initial["description"],
            "Original milestone description.",
        )

        self.assertEqual(
            response.context["form"].initial["due_date"],
            date(2026, 9, 30),
        )

    def test_valid_milestone_edit(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        new_due_date = date(2026, 10, 15)

        response = self.client.post(
            self.edit_url,
            {
                "title": "Project Foundation Setup",
                "description": "Updated milestone description.",
                "due_date": new_due_date.isoformat(),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.milestone.refresh_from_db()

        self.assertEqual(
            self.milestone.title,
            "Project Foundation Setup",
        )

        self.assertEqual(
            self.milestone.description,
            "Updated milestone description.",
        )

        self.assertEqual(
            self.milestone.due_date,
            new_due_date,
        )

        self.assertEqual(
            Milestone.objects.count(),
            1,
        )

    def test_non_member_cannot_edit_milestone(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.get(
            self.edit_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        response = self.client.post(
            self.edit_url,
            {
                "title": "Unauthorized Edit",
                "description": "This change should not be saved.",
                "due_date": "2026-11-01",
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.milestone.refresh_from_db()

        self.assertEqual(
            self.milestone.title,
            "Initial Project Setup",
        )

        self.assertEqual(
            self.milestone.description,
            "Original milestone description.",
        )

        self.assertEqual(
            self.milestone.due_date,
            date(2026, 9, 30),
        )

    def test_edit_title_is_required(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.edit_url,
            {
                "title": "",
                "description": "Updated description.",
                "due_date": "2026-10-15",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["form"]

        self.assertIn(
            "This field is required.",
            form.errors["title"],
        )

        self.milestone.refresh_from_db()

        self.assertEqual(
            self.milestone.title,
            "Initial Project Setup",
        )

        self.assertEqual(
            self.milestone.description,
            "Original milestone description.",
        )

        self.assertEqual(
            self.milestone.due_date,
            date(2026, 9, 30),
        )

    def test_milestone_from_different_project_cannot_be_edited(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        second_milestone = Milestone.objects.create(
            project=second_project,
            title="Second Project Milestone",
            description="Second project milestone.",
            due_date=date(2026, 11, 1),
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        wrong_project_url = reverse(
            "workspaces:milestone_edit",
            kwargs={
                "slug": self.project.slug,
                "milestone_id": second_milestone.pk,
            },
        )

        response = self.client.get(
            wrong_project_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        response = self.client.post(
            wrong_project_url,
            {
                "title": "Wrong Project Edit",
                "description": "This should not be saved.",
                "due_date": "2026-12-01",
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        second_milestone.refresh_from_db()

        self.assertEqual(
            second_milestone.title,
            "Second Project Milestone",
        )

        self.assertEqual(
            second_milestone.description,
            "Second project milestone.",
        )

        self.assertEqual(
            second_milestone.due_date,
            date(2026, 11, 1),
        )


class MilestoneDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.milestone = Milestone.objects.create(
            project=self.project,
            title="Initial Project Setup",
            description="Milestone to delete.",
            due_date=date(2026, 9, 30),
        )

        self.delete_url = reverse(
            "workspaces:milestone_delete",
            kwargs={
                "slug": self.project.slug,
                "milestone_id": self.milestone.pk,
            },
        )

    def test_logged_out_user_cannot_delete_milestone(self):
        response = self.client.post(
            self.delete_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

        self.assertTrue(
            Milestone.objects.filter(
                pk=self.milestone.pk,
            ).exists()
        )

    def test_project_member_can_delete_milestone(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.delete_url,
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertFalse(
            Milestone.objects.filter(
                pk=self.milestone.pk,
            ).exists()
        )

    def test_get_does_not_delete_milestone(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(
            self.delete_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertTrue(
            Milestone.objects.filter(
                pk=self.milestone.pk,
            ).exists()
        )

    def test_non_member_cannot_delete_milestone(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.post(
            self.delete_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertTrue(
            Milestone.objects.filter(
                pk=self.milestone.pk,
            ).exists()
        )

    def test_milestone_from_different_project_cannot_be_deleted(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        second_milestone = Milestone.objects.create(
            project=second_project,
            title="Second Project Milestone",
            description="Second project milestone.",
            due_date=date(2026, 11, 1),
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        wrong_project_url = reverse(
            "workspaces:milestone_delete",
            kwargs={
                "slug": self.project.slug,
                "milestone_id": second_milestone.pk,
            },
        )

        response = self.client.post(
            wrong_project_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertTrue(
            Milestone.objects.filter(
                pk=second_milestone.pk,
            ).exists()
        )


class TaskDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.milestone = Milestone.objects.create(
            project=self.project,
            title="Initial Project Setup",
            description="Project foundation milestone.",
            due_date=date(2026, 9, 30),
        )

        self.task = Task.objects.create(
            project=self.project,
            milestone=self.milestone,
            title="Implement authentication",
            description="Build login and registration.",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.HIGH,
            assignee=self.user,
            created_by=self.user,
        )

        self.detail_url = reverse(
            "workspaces:task_detail",
            kwargs={
                "slug": self.project.slug,
                "task_id": self.task.pk,
            },
        )

    def test_logged_out_user_cannot_view_task_detail(self):
        response = self.client.get(
            self.detail_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

    def test_project_member_can_view_task_detail(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(
            self.detail_url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "workspaces/task_detail.html",
        )

        self.assertEqual(
            response.context["project"],
            self.project,
        )

        self.assertEqual(
            response.context["task"],
            self.task,
        )

    def test_task_detail_displays_task_information(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(
            self.detail_url,
        )

        self.assertContains(
            response,
            "Implement authentication",
        )

        self.assertContains(
            response,
            "Build login and registration.",
        )

        self.assertContains(
            response,
            "In progress",
        )

        self.assertContains(
            response,
            "High",
        )

        self.assertContains(
            response,
            "Initial Project Setup",
        )

        self.assertContains(
            response,
            "owner",
        )

    def test_non_member_cannot_view_task_detail(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.get(
            self.detail_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

    def test_task_from_different_project_cannot_be_viewed(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        second_task = Task.objects.create(
            project=second_project,
            title="Second Project Task",
            description="Task belongs to another project.",
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
            created_by=self.user,
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        wrong_project_url = reverse(
            "workspaces:task_detail",
            kwargs={
                "slug": self.project.slug,
                "task_id": second_task.pk,
            },
        )

        response = self.client.get(
            wrong_project_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class TaskCommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Implement authentication",
            description="Build login and registration.",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.HIGH,
            assignee=self.user,
            created_by=self.user,
        )

        self.comment_data = {
            "body": "Authentication implementation looks good.",
        }

        self.task_url = reverse(
            "workspaces:task_detail",
            kwargs={
                "slug": self.project.slug,
                "task_id": self.task.pk,
            },
        )

    def test_logged_out_user_cannot_add_comment(self):
        response = self.client.post(
            self.task_url,
            self.comment_data,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

        self.assertEqual(
            Comment.objects.filter(
                task=self.task,
            ).count(),
            0,
        )

    def test_project_member_can_add_comment(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.task_url,
            self.comment_data,
        )

        self.assertRedirects(
            response,
            self.task_url,
        )

        self.assertEqual(
            Comment.objects.filter(
                task=self.task,
            ).count(),
            1,
        )

        comment = Comment.objects.get(
            task=self.task,
        )

        self.assertEqual(
            comment.body,
            "Authentication implementation looks good.",
        )

        self.assertEqual(
            comment.task,
            self.task,
        )

        self.assertEqual(
            comment.author,
            self.user,
        )

    def test_empty_comment_is_rejected(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.task_url,
            {
                "body": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["comment_form"]

        self.assertIn(
            "This field is required.",
            form.errors["body"],
        )

        self.assertEqual(
            Comment.objects.filter(
                task=self.task,
            ).count(),
            0,
        )

    def test_non_member_cannot_add_comment(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.post(
            self.task_url,
            self.comment_data,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertEqual(
            Comment.objects.filter(
                task=self.task,
            ).count(),
            0,
        )

    def test_comment_belongs_to_correct_task(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.task_url,
            self.comment_data,
        )

        self.assertRedirects(
            response,
            self.task_url,
        )

        comment = Comment.objects.get(
            task=self.task,
        )

        self.assertEqual(
            comment.task.pk,
            self.task.pk,
        )

        self.assertEqual(
            comment.author.pk,
            self.user.pk,
        )

    def test_comment_cannot_be_added_to_task_from_different_project(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        second_task = Task.objects.create(
            project=second_project,
            title="Second Project Task",
            description="Task belongs to another project.",
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
            created_by=self.user,
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        wrong_project_url = reverse(
            "workspaces:task_detail",
            kwargs={
                "slug": self.project.slug,
                "task_id": second_task.pk,
            },
        )

        response = self.client.post(
            wrong_project_url,
            self.comment_data,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            Comment.objects.filter(
                task=second_task,
            ).count(),
            0,
        )


class TaskEditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.milestone = Milestone.objects.create(
            project=self.project,
            title="Initial Project Setup",
            description="Project foundation milestone.",
            due_date=date(2026, 9, 30),
        )

        self.task = Task.objects.create(
            project=self.project,
            milestone=self.milestone,
            title="Implement authentication",
            description="Build login and registration.",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.HIGH,
            assignee=self.user,
            created_by=self.user,
        )

        self.edit_url = reverse(
            "workspaces:task_edit",
            kwargs={
                "slug": self.project.slug,
                "task_id": self.task.pk,
            },
        )

    def test_project_member_can_open_task_edit_form(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(self.edit_url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "workspaces/task_form.html",
        )

        self.assertTrue(
            response.context["is_edit"],
        )

        self.assertEqual(
            response.context["task"],
            self.task,
        )

        self.assertEqual(
            response.context["form"].initial["title"],
            "Implement authentication",
        )

        self.assertEqual(
            response.context["form"].initial["description"],
            "Build login and registration.",
        )

        self.assertEqual(
            response.context["form"].initial["status"],
            Task.Status.IN_PROGRESS,
        )

        self.assertEqual(
            response.context["form"].initial["priority"],
            Task.Priority.HIGH,
        )

        self.assertEqual(
            response.context["form"].initial["milestone"],
            self.milestone.pk,
        )

        self.assertEqual(
            response.context["form"].initial["assignee"],
            self.user.pk,
        )

    def test_valid_task_edit(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.edit_url,
            {
                "milestone": self.milestone.pk,
                "title": "Implement complete authentication",
                "description": "Updated authentication implementation.",
                "status": Task.Status.DONE,
                "priority": Task.Priority.MEDIUM,
                "assignee": self.user.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.title,
            "Implement complete authentication",
        )

        self.assertEqual(
            self.task.description,
            "Updated authentication implementation.",
        )

        self.assertEqual(
            self.task.status,
            Task.Status.DONE,
        )

        self.assertEqual(
            self.task.priority,
            Task.Priority.MEDIUM,
        )

        self.assertEqual(
            self.task.milestone,
            self.milestone,
        )

        self.assertEqual(
            self.task.assignee,
            self.user,
        )

        self.assertEqual(
            self.task.project,
            self.project,
        )

    def test_non_member_cannot_edit_task(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.get(
            self.edit_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        response = self.client.post(
            self.edit_url,
            {
                "milestone": self.milestone.pk,
                "title": "Unauthorized Edit",
                "description": "This should not be saved.",
                "status": Task.Status.DONE,
                "priority": Task.Priority.LOW,
                "assignee": "",
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.title,
            "Implement authentication",
        )

        self.assertEqual(
            self.task.description,
            "Build login and registration.",
        )

        self.assertEqual(
            self.task.status,
            Task.Status.IN_PROGRESS,
        )

        self.assertEqual(
            self.task.priority,
            Task.Priority.HIGH,
        )

    def test_task_from_different_project_cannot_be_edited(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        second_task = Task.objects.create(
            project=second_project,
            title="Second Project Task",
            description="Task belongs to another project.",
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
            created_by=self.user,
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        wrong_project_url = reverse(
            "workspaces:task_edit",
            kwargs={
                "slug": self.project.slug,
                "task_id": second_task.pk,
            },
        )

        response = self.client.get(
            wrong_project_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        response = self.client.post(
            wrong_project_url,
            {
                "title": "Wrong Project Edit",
                "description": "This should not be saved.",
                "status": Task.Status.DONE,
                "priority": Task.Priority.HIGH,
                "assignee": "",
                "milestone": "",
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        second_task.refresh_from_db()

        self.assertEqual(
            second_task.title,
            "Second Project Task",
        )

        self.assertEqual(
            second_task.description,
            "Task belongs to another project.",
        )

        self.assertEqual(
            second_task.status,
            Task.Status.TODO,
        )

        self.assertEqual(
            second_task.priority,
            Task.Priority.MEDIUM,
        )

    def test_edit_task_title_is_required(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.edit_url,
            {
                "milestone": self.milestone.pk,
                "title": "",
                "description": "Updated description.",
                "status": Task.Status.DONE,
                "priority": Task.Priority.MEDIUM,
                "assignee": self.user.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        form = response.context["form"]

        self.assertIn(
            "This field is required.",
            form.errors["title"],
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.title,
            "Implement authentication",
        )

        self.assertEqual(
            self.task.description,
            "Build login and registration.",
        )

        self.assertEqual(
            self.task.status,
            Task.Status.IN_PROGRESS,
        )

        self.assertEqual(
            self.task.priority,
            Task.Priority.HIGH,
        )


class TaskDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Implement authentication",
            description="Build login and registration.",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.HIGH,
            assignee=self.user,
            created_by=self.user,
        )

        self.delete_url = reverse(
            "workspaces:task_delete",
            kwargs={
                "slug": self.project.slug,
                "task_id": self.task.pk,
            },
        )

    def test_logged_out_user_cannot_delete_task(self):
        response = self.client.post(
            self.delete_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

        self.assertTrue(
            Task.objects.filter(
                pk=self.task.pk,
            ).exists()
        )

    def test_project_member_can_delete_task(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.delete_url,
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertFalse(
            Task.objects.filter(
                pk=self.task.pk,
            ).exists()
        )

    def test_get_does_not_delete_task(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.get(
            self.delete_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertTrue(
            Task.objects.filter(
                pk=self.task.pk,
            ).exists()
        )

    def test_non_member_cannot_delete_task(self):
        self.client.login(
            username="other-user",
            password="test-password-123",
        )

        response = self.client.post(
            self.delete_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertTrue(
            Task.objects.filter(
                pk=self.task.pk,
            ).exists()
        )

    def test_task_from_different_project_cannot_be_deleted(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.user,
            role=ProjectMembership.Role.LEAD,
        )

        second_task = Task.objects.create(
            project=second_project,
            title="Second Project Task",
            description="Task belongs to another project.",
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
            created_by=self.user,
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        wrong_project_url = reverse(
            "workspaces:task_delete",
            kwargs={
                "slug": self.project.slug,
                "task_id": second_task.pk,
            },
        )

        response = self.client.post(
            wrong_project_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertTrue(
            Task.objects.filter(
                pk=second_task.pk,
            ).exists()
        )


class MemberManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="test-password-123",
        )

        self.member = User.objects.create_user(
            username="member",
            password="test-password-123",
        )

        self.other_user = User.objects.create_user(
            username="other-user",
            password="test-password-123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.owner,
        )

        self.owner_membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.owner,
            role=ProjectMembership.Role.LEAD,
        )

        self.add_url = reverse(
            "workspaces:member_add",
            kwargs={
                "slug": self.project.slug,
            },
        )

    def test_logged_out_user_cannot_add_member(self):
        response = self.client.post(
            self.add_url,
            {
                "user": self.member.pk,
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

        self.assertFalse(
            ProjectMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

    def test_owner_can_add_member(self):
        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.add_url,
            {
                "user": self.member.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        membership = ProjectMembership.objects.get(
            project=self.project,
            user=self.member,
        )

        self.assertEqual(
            membership.role,
            ProjectMembership.Role.MEMBER,
        )

    def test_non_owner_cannot_add_member(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.login(
            username="member",
            password="test-password-123",
        )

        response = self.client.post(
            self.add_url,
            {
                "user": self.other_user.pk,
            },
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertFalse(
            ProjectMembership.objects.filter(
                project=self.project,
                user=self.other_user,
            ).exists()
        )

    def test_existing_member_is_excluded_from_member_form(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        form = MemberForm(
            project=self.project,
        )

        user_field = cast(
            forms.ModelChoiceField,
            form.fields["user"],
        )

        queryset = user_field.queryset

        if queryset is None:
            raise AssertionError(
                "MemberForm user field queryset must not be None."
            )

        self.assertNotIn(
            self.member,
            queryset,
        )

        self.assertIn(
            self.other_user,
            queryset,
        )

    def test_duplicate_membership_is_rejected_by_form(self):
        ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        form = MemberForm(
            data={
                "user": self.member.pk,
            },
            project=self.project,
        )

        self.assertFalse(
            form.is_valid(),
        )

        self.assertIn(
            "user",
            form.errors,
        )

    def test_owner_can_remove_member(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": membership.pk,
            },
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            remove_url,
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertFalse(
            ProjectMembership.objects.filter(
                pk=membership.pk,
            ).exists()
        )

    def test_non_owner_cannot_remove_member(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": membership.pk,
            },
        )

        self.client.login(
            username="member",
            password="test-password-123",
        )

        response = self.client.post(
            remove_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                pk=membership.pk,
            ).exists()
        )

    def test_owner_cannot_remove_themselves(self):
        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": self.owner_membership.pk,
            },
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            remove_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                pk=self.owner_membership.pk,
            ).exists()
        )

    def test_logged_out_user_cannot_remove_member(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": membership.pk,
            },
        )

        response = self.client.post(
            remove_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/accounts/login/",
            response.headers["Location"],
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                pk=membership.pk,
            ).exists()
        )

    def test_member_from_another_project_can_be_added(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.other_user,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.other_user,
            role=ProjectMembership.Role.LEAD,
        )

        ProjectMembership.objects.create(
            project=second_project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            self.add_url,
            {
                "user": self.member.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "workspaces:project_detail",
                kwargs={
                    "slug": self.project.slug,
                },
            ),
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                project=self.project,
                user=self.member,
            ).exists()
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                project=second_project,
                user=self.member,
            ).exists()
        )

    def test_removed_member_loses_private_project_access(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        project_url = reverse(
            "workspaces:project_detail",
            kwargs={
                "slug": self.project.slug,
            },
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": membership.pk,
            },
        )

        self.client.post(remove_url)

        self.client.login(
            username="member",
            password="test-password-123",
        )

        response = self.client.get(
            project_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.headers["Location"],
            reverse(
                "accounts:dashboard",
            ),
        )

    def test_removing_member_does_not_delete_user(self):
        membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": membership.pk,
            },
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        self.client.post(remove_url)

        self.assertTrue(
            User.objects.filter(
                pk=self.member.pk,
            ).exists()
        )

    def test_membership_from_another_project_cannot_be_removed(self):
        second_project = Project.objects.create(
            name="Second Project",
            description="Second project description",
            visibility=Project.Visibility.PRIVATE,
            owner=self.owner,
        )

        second_membership = ProjectMembership.objects.create(
            project=second_project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        remove_url = reverse(
            "workspaces:member_remove",
            kwargs={
                "slug": self.project.slug,
                "membership_id": second_membership.pk,
            },
        )

        self.client.login(
            username="owner",
            password="test-password-123",
        )

        response = self.client.post(
            remove_url,
            follow=False,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                pk=second_membership.pk,
            ).exists()
        )
        