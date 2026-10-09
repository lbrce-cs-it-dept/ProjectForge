from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from workspaces.models import (
    Milestone,
    Notification,
    ProjectMembership,
)


class Command(BaseCommand):
    help = "Create notifications for milestones due today."

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.localdate()

        milestones = Milestone.objects.filter(
            due_date=today,
        ).select_related(
            "project",
            "project__owner",
        )

        created_count = 0

        for milestone in milestones:
            project = milestone.project

            # Include all current project members.
            recipient_ids = set(
                ProjectMembership.objects.filter(
                    project=project,
                ).values_list(
                    "user_id",
                    flat=True,
                )
            )

            # Ensure the project owner receives the notification too.
            recipient_ids.add(project.owner.pk)

            target_url = reverse(
                "workspaces:project_detail",
                kwargs={"slug": project.slug},
            )

            message = (
                f'"{milestone.title}" is due today '
                f'in {project.name}.'
            )[:300]

            for recipient_id in recipient_ids:
                _, created = Notification.objects.get_or_create(
                    recipient_id=recipient_id,
                    notification_type=(
                        Notification.Type.MILESTONE_DUE
                    ),
                    milestone=milestone,
                    defaults={
                        "title": "Milestone due today",
                        "message": message,
                        "target_url": target_url,
                    },
                )

                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} milestone due "
                f"notification(s) for {today}."
            )
        )
