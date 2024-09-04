from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import format_html
from loguru import logger
from notes.models import Note



@shared_task
def send_reminder_email(note_id):
    """
        A Celery task to send a plain text reminder email to the user.

    """
    try:
        note = Note.objects.get(id=note_id)
        user_email = note.user.email
        body=f"Reminder for Note: {note.title} - {note.reminder}"
        subject = f"Reminder"
        send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )
    except Exception as e:
        logger.info("Note not found")
    
