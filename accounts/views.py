from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from workspaces.models import Milestone, Project, Task

from .forms import SignUpForm


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("accounts:dashboard")

        return render(
            request,
            "accounts/login.html",
            {"error": "Invalid username or password."},
        )

    return render(request, "accounts/login.html")


def signup_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
            )

            return redirect("accounts:dashboard")
    else:
        form = SignUpForm()

    return render(
        request,
        "accounts/signup.html",
        {"form": form},
    )


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(
            "Method Not Allowed",
            status=405,
        )

    logout(request)

    return redirect("workspaces:home")


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    user = request.user

    owned_projects = Project.objects.filter(
        owner=user,
    )

    member_projects = Project.objects.filter(
        memberships__user=user,
    )

    projects = (
        owned_projects | member_projects
    ).distinct()

    project_count = projects.count()

    task_count = Task.objects.filter(
        project__in=projects,
        assignee=user,
    ).count()

    milestone_count = Milestone.objects.filter(
        project__in=projects,
        due_date__isnull=False,
    ).count()

    return render(
        request,
        "accounts/dashboard.html",
        {
            "projects": projects,
            "project_count": project_count,
            "task_count": task_count,
            "milestone_count": milestone_count,
        },
    )
