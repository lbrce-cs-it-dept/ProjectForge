from django.contrib import admin

from .models import Comment, Milestone, Project, ProjectMembership, Task

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "visibility",
        "created_at",
        "updated_at",
    )
    list_filter = ("visibility", "created_at")
    search_fields = ("name", "description", "owner__username")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "role", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("project__name", "user__username", "user__email")
    readonly_fields = ("joined_at",)

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "due_date", "created_at")
    list_filter = ("project", "due_date")
    search_fields = ("title", "description", "project__name")
    readonly_fields = ("created_at", "updated_at")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "status",
        "priority",
        "assignee",
        "updated_at",
    )
    list_filter = ("status", "priority", "project")
    search_fields = (
        "title",
        "description",
        "project__name",
        "assignee__username",
    )
    readonly_fields = ("created_at", "updated_at")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "short_body", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "task__title", "author__username")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Comment")
    def short_body(self, obj):
        return obj.body[:70]