from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, max_length=140)
    description = models.TextField(max_length=2000)
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        LEAD = "lead", "Lead"
        MEMBER = "member", "Member"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_membership",
            )
        ]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} → {self.project.name} ({self.role})"


class Milestone(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=120)
    description = models.TextField(max_length=1000, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "created_at"]

    def __str__(self):
        return f"{self.project.name} — {self.title}"


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=180)
    description = models.TextField(max_length=3000, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-updated_at"]

    def __str__(self):
        return f"{self.project.name} — {self.title}"


class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username} on {self.task.title}"


class Activity(models.Model):
    class Action(models.TextChoices):
        PROJECT_CREATED = "project_created", "Project created"
        PROJECT_UPDATED = "project_updated", "Project updated"
        MEMBER_ADDED = "member_added", "Member added"
        MEMBER_REMOVED = "member_removed", "Member removed"
        MILESTONE_CREATED = "milestone_created", "Milestone created"
        MILESTONE_UPDATED = "milestone_updated", "Milestone updated"
        MILESTONE_DELETED = "milestone_deleted", "Milestone deleted"
        TASK_CREATED = "task_created", "Task created"
        TASK_UPDATED = "task_updated", "Task updated"
        TASK_ASSIGNED = "task_assigned", "Task assigned"
        TASK_COMPLETED = "task_completed", "Task completed"
        TASK_DELETED = "task_deleted", "Task deleted"
        COMMENT_ADDED = "comment_added", "Comment added"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="project_activities",
        null=True,
        blank=True,
    )
    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )
    description = models.CharField(
        max_length=300,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.name} — {self.description}"


class Notification(models.Model):
    class Type(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task assigned"
        COMMENT_ADDED = "comment_added", "Comment added"
        MEMBER_ADDED = "member_added", "Member added"
        TASK_COMPLETED = "task_completed", "Task completed"
        MILESTONE_DUE = "milestone_due", "Milestone due"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
    )
    title = models.CharField(
        max_length=180,
    )
    message = models.CharField(
        max_length=300,
    )
    target_url = models.CharField(
        max_length=500,
        blank=True,
    )
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    is_read = models.BooleanField(
        default=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "recipient",
                    "notification_type",
                    "milestone",
                ],
                name="unique_milestone_notification_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.recipient.username} — {self.title}"
