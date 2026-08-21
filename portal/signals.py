from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StudentProfile


def create_student_profile(user):
    """Give every non-staff user a portal profile when their account is created."""
    if user.is_staff or StudentProfile.objects.filter(user=user).exists():
        return
    StudentProfile.objects.create(
        user=user,
        student_id=f"EPM-{user.pk:06d}",
        current_class='JSS 1',
    )


@receiver(post_save, sender=User)
def create_student_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        create_student_profile(instance)
