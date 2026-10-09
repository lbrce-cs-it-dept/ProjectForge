from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    CommentForm,
    MemberForm,
    MilestoneForm,
    ProjectForm,
    TaskForm,
)
from .models import (
    Activity,
    Comment,
    Milestone,
    Notification,
    Project,
    ProjectMembership,
    Task,
)


def create_activity(
    project,
    actor,
    action,
    description,
):
    return Activity.objects.create(
        project=project,
        actor=actor,
        action=action,
        description=description,
    )


def create_notification(
    recipient,
    notification_type,
    title,
    message,
    target_url="",
):
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        target_url=target_url,
    )


def home(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "workspaces/home.html",
    )


@login_required
def notifications(
    request: HttpRequest,
) -> HttpResponse:
    user_notifications = (
        Notification.objects.filter(
            recipient=request.user,
        )
        .select_related("recipient")
        .all()
    )

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()

    return render(
        request,
        "workspaces/notifications.html",
        {
            "notifications": user_notifications,
            "unread_count": unread_count,
        },
    )


@login_required
@transaction.atomic
def notification_read(
    request: HttpRequest,
    notification_id: int,
) -> HttpResponse:
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    if request.method == "POST":
        notification.is_read = True
        notification.save(
            update_fields=["is_read"],
        )

        if notification.target_url:
            return redirect(
                notification.target_url,
            )

        return redirect(
            "workspaces:notifications",
        )

    return redirect(
        "workspaces:notifications",
    )


@login_required
@transaction.atomic
def notifications_read_all(
    request: HttpRequest,
) -> HttpResponse:
    if request.method == "POST":
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
        )

    return redirect(
        "workspaces:notifications",
    )


@login_required
@transaction.atomic
def project_create(
    request: HttpRequest,
) -> HttpResponse:
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(
                commit=False,
            )

            project.owner = request.user
            project.save()

            ProjectMembership.objects.create(
                project=project,
                user=request.user,
                role=ProjectMembership.Role.LEAD,
            )

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.PROJECT_CREATED,
                description=(
                    f"{request.user.username} created the project."
                ),
            )

            return redirect(
                "accounts:dashboard",
            )
    else:
        form = ProjectForm()

    return render(
        request,
        "workspaces/project_form.html",
        {
            "form": form,
        },
    )


@login_required
def project_detail(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if (
        project.visibility == Project.Visibility.PRIVATE
        and not is_member
    ):
        return redirect(
            "accounts:dashboard",
        )

    members = (
        ProjectMembership.objects.filter(
            project=project,
        )
        .select_related("user")
        .order_by(
            "role",
            "user__username",
        )
    )

    member_form = None

    if project.owner == request.user:
        member_form = MemberForm(
            project=project,
        )

    activities = (
        Activity.objects.filter(
            project=project,
        )
        .select_related("actor")
        .all()[:20]
    )

    return render(
        request,
        "workspaces/project_detail.html",
        {
            "project": project,
            "members": members,
            "member_form": member_form,
            "activities": activities,
        },
    )


@login_required
@transaction.atomic
def project_edit(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    if project.owner != request.user:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method == "POST":
        form = ProjectForm(
            request.POST,
            instance=project,
        )

        if form.is_valid():
            form.save()

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.PROJECT_UPDATED,
                description=(
                    f"{request.user.username} updated the project."
                ),
            )

            return redirect(
                "workspaces:project_detail",
                slug=project.slug,
            )
    else:
        form = ProjectForm(
            instance=project,
        )

    return render(
        request,
        "workspaces/project_form.html",
        {
            "form": form,
            "project": project,
            "is_edit": True,
        },
    )


@login_required
@transaction.atomic
def project_delete(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    if project.owner != request.user:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method != "POST":
        return HttpResponse(
            "Method Not Allowed",
            status=405,
        )

    project.delete()

    return redirect(
        "accounts:dashboard",
    )


@login_required
@transaction.atomic
def member_add(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    if project.owner != request.user:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method == "POST":
        form = MemberForm(
            request.POST,
            project=project,
        )

        if form.is_valid():
            user = form.cleaned_data["user"]

            ProjectMembership.objects.create(
                project=project,
                user=user,
                role=ProjectMembership.Role.MEMBER,
            )

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.MEMBER_ADDED,
                description=(
                    f"{request.user.username} added "
                    f"{user.username} to the project."
                ),
            )

            create_notification(
                recipient=user,
                notification_type=Notification.Type.MEMBER_ADDED,
                title="Added to a project",
                message=(
                    f"{request.user.username} added you to "
                    f"the project '{project.name}'."
                ),
                target_url=reverse(
                    "workspaces:project_detail",
                    kwargs={
                        "slug": project.slug,
                    },
                ),
            )

    return redirect(
        "workspaces:project_detail",
        slug=project.slug,
    )


@login_required
@transaction.atomic
def member_remove(
    request: HttpRequest,
    slug: str,
    membership_id: int,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    membership = get_object_or_404(
        ProjectMembership,
        id=membership_id,
        project=project,
    )

    if project.owner != request.user:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if membership.user == project.owner:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method != "POST":
        return HttpResponse(
            "Method Not Allowed",
            status=405,
        )

    removed_username = membership.user.username

    membership.delete()

    create_activity(
        project=project,
        actor=request.user,
        action=Activity.Action.MEMBER_REMOVED,
        description=(
            f"{request.user.username} removed "
            f"{removed_username} from the project."
        ),
    )

    return redirect(
        "workspaces:project_detail",
        slug=project.slug,
    )


@login_required
@transaction.atomic
def milestone_create(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method == "POST":
        form = MilestoneForm(
            request.POST,
        )

        if form.is_valid():
            milestone = form.save(
                commit=False,
            )

            milestone.project = project
            milestone.save()

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.MILESTONE_CREATED,
                description=(
                    f"{request.user.username} created "
                    f"milestone '{milestone.title}'."
                ),
            )

            return redirect(
                "workspaces:project_detail",
                slug=project.slug,
            )
    else:
        form = MilestoneForm()

    return render(
        request,
        "workspaces/milestone_form.html",
        {
            "form": form,
            "project": project,
            "is_edit": False,
        },
    )


@login_required
@transaction.atomic
def milestone_edit(
    request: HttpRequest,
    slug: str,
    milestone_id: int,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    milestone = get_object_or_404(
        Milestone,
        id=milestone_id,
        project=project,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method == "POST":
        form = MilestoneForm(
            request.POST,
            instance=milestone,
        )

        if form.is_valid():
            form.save()

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.MILESTONE_UPDATED,
                description=(
                    f"{request.user.username} updated "
                    f"milestone '{milestone.title}'."
                ),
            )

            return redirect(
                "workspaces:project_detail",
                slug=project.slug,
            )
    else:
        form = MilestoneForm(
            instance=milestone,
        )

    return render(
        request,
        "workspaces/milestone_form.html",
        {
            "form": form,
            "project": project,
            "milestone": milestone,
            "is_edit": True,
        },
    )


@login_required
@transaction.atomic
def milestone_delete(
    request: HttpRequest,
    slug: str,
    milestone_id: int,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    milestone = get_object_or_404(
        Milestone,
        id=milestone_id,
        project=project,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method != "POST":
        return HttpResponse(
            "Method Not Allowed",
            status=405,
        )

    milestone_title = milestone.title

    milestone.delete()

    create_activity(
        project=project,
        actor=request.user,
        action=Activity.Action.MILESTONE_DELETED,
        description=(
            f"{request.user.username} deleted "
            f"milestone '{milestone_title}'."
        ),
    )

    return redirect(
        "workspaces:project_detail",
        slug=project.slug,
    )


@login_required
@transaction.atomic
def task_create(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            project=project,
        )

        if form.is_valid():
            task = form.save(
                commit=False,
            )

            task.project = project
            task.created_by = request.user
            task.save()

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.TASK_CREATED,
                description=(
                    f"{request.user.username} created "
                    f"task '{task.title}'."
                ),
            )

            if task.assignee is not None:
                create_activity(
                    project=project,
                    actor=request.user,
                    action=Activity.Action.TASK_ASSIGNED,
                    description=(
                        f"{request.user.username} assigned "
                        f"task '{task.title}' to "
                        f"{task.assignee.username}."
                    ),
                )

                if task.assignee != request.user:
                    create_notification(
                        recipient=task.assignee,
                        notification_type=Notification.Type.TASK_ASSIGNED,
                        title="Task assigned to you",
                        message=(
                            f"{request.user.username} assigned "
                            f"'{task.title}' to you."
                        ),
                        target_url=(
                            f"/projects/{project.slug}/"
                            f"tasks/{task.pk}/"
                        ),
                    )

            if task.status == Task.Status.DONE:
                create_activity(
                    project=project,
                    actor=request.user,
                    action=Activity.Action.TASK_COMPLETED,
                    description=(
                        f"{request.user.username} completed "
                        f"task '{task.title}'."
                    ),
                )

            return redirect(
                "workspaces:project_detail",
                slug=project.slug,
            )
    else:
        form = TaskForm(
            project=project,
        )

    return render(
        request,
        "workspaces/task_form.html",
        {
            "form": form,
            "project": project,
        },
    )


@login_required
@transaction.atomic
def task_edit(
    request: HttpRequest,
    slug: str,
    task_id: int,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    task = get_object_or_404(
        Task,
        id=task_id,
        project=project,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    old_status = task.status
    old_assignee = task.assignee

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
            project=project,
        )

        if form.is_valid():
            form.save()

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.TASK_UPDATED,
                description=(
                    f"{request.user.username} updated "
                    f"task '{task.title}'."
                ),
            )

            if old_assignee != task.assignee:
                if task.assignee is None:
                    assignment_description = (
                        f"{request.user.username} unassigned "
                        f"task '{task.title}'."
                    )
                else:
                    assignment_description = (
                        f"{request.user.username} assigned "
                        f"task '{task.title}' to "
                        f"{task.assignee.username}."
                    )

                create_activity(
                    project=project,
                    actor=request.user,
                    action=Activity.Action.TASK_ASSIGNED,
                    description=assignment_description,
                )

                if (
                    task.assignee is not None
                    and task.assignee != request.user
                ):
                    create_notification(
                        recipient=task.assignee,
                        notification_type=Notification.Type.TASK_ASSIGNED,
                        title="Task assigned to you",
                        message=(
                            f"{request.user.username} assigned "
                            f"'{task.title}' to you."
                        ),
                        target_url=reverse(
                            "workspaces:task_detail",
                            kwargs={
                                "slug": project.slug,
                                "task_id": task.pk,
                            },
                        ),
                    )

            if (
                old_status != Task.Status.DONE
                and task.status == Task.Status.DONE
            ):
                create_activity(
                    project=project,
                    actor=request.user,
                    action=Activity.Action.TASK_COMPLETED,
                    description=(
                        f"{request.user.username} completed "
                        f"task '{task.title}'."
                    ),
                )

                recipients = {
                    task.created_by,
                }

                if task.assignee is not None:
                    recipients.add(
                        task.assignee,
                    )

                recipients.discard(
                    request.user,
                )

                for recipient in recipients:
                    create_notification(
                        recipient=recipient,
                        notification_type=(
                            Notification.Type.TASK_COMPLETED
                        ),
                        title="Task completed",
                        message=(
                            f"{request.user.username} completed "
                            f"'{task.title}'."
                        ),
                        target_url=(
                            f"/projects/{project.slug}/"
                            f"tasks/{task.pk}/"
                        ),
                    )

            return redirect(
                "workspaces:project_detail",
                slug=project.slug,
            )
    else:
        form = TaskForm(
            instance=task,
            project=project,
        )

    return render(
        request,
        "workspaces/task_form.html",
        {
            "form": form,
            "project": project,
            "task": task,
            "is_edit": True,
        },
    )


@login_required
def task_detail(
    request: HttpRequest,
    slug: str,
    task_id: int,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    task = get_object_or_404(
        Task,
        pk=task_id,
        project=project,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method == "POST":
        form = CommentForm(
            request.POST,
        )

        if form.is_valid():
            comment = form.save(
                commit=False,
            )

            comment.task = task
            comment.author = request.user
            comment.save()

            create_activity(
                project=project,
                actor=request.user,
                action=Activity.Action.COMMENT_ADDED,
                description=(
                    f"{request.user.username} commented "
                    f"on task '{task.title}'."
                ),
            )

            recipients = {
                task.created_by,
            }

            if task.assignee is not None:
                recipients.add(
                    task.assignee,
                )

            for existing_comment in Comment.objects.filter(
                task=task,
            ).exclude(
                author=request.user,
            ):
                recipients.add(
                    existing_comment.author,
                )

            recipients.discard(
                request.user,
            )

            for recipient in recipients:
                create_notification(
                    recipient=recipient,
                    notification_type=Notification.Type.COMMENT_ADDED,
                    title="New comment",
                    message=(
                        f"{request.user.username} commented "
                        f"on '{task.title}'."
                    ),
                    target_url=(
                        f"/projects/{project.slug}/"
                        f"tasks/{task.pk}/"
                    ),
                )

            return redirect(
                "workspaces:task_detail",
                slug=project.slug,
                task_id=task.pk,
            )
    else:
        form = CommentForm()

    comments = (
        Comment.objects.filter(
            task=task,
        )
        .select_related("author")
        .all()
    )

    return render(
        request,
        "workspaces/task_detail.html",
        {
            "project": project,
            "task": task,
            "comments": comments,
            "comment_form": form,
        },
    )


@login_required
@transaction.atomic
def task_delete(
    request: HttpRequest,
    slug: str,
    task_id: int,
) -> HttpResponse:
    project = get_object_or_404(
        Project,
        slug=slug,
    )

    task = get_object_or_404(
        Task,
        id=task_id,
        project=project,
    )

    is_member = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
    ).exists()

    if not is_member:
        return redirect(
            "workspaces:project_detail",
            slug=project.slug,
        )

    if request.method != "POST":
        return HttpResponse(
            "Method Not Allowed",
            status=405,
        )

    task_title = task.title

    task.delete()

    create_activity(
        project=project,
        actor=request.user,
        action=Activity.Action.TASK_DELETED,
        description=(
            f"{request.user.username} deleted "
            f"task '{task_title}'."
        ),
    )

    return redirect(
        "workspaces:project_detail",
        slug=project.slug,
    )
