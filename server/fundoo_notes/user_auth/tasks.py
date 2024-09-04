from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import format_html

@shared_task
def send_verification_email(user_email, verification_link):
    """
    A Celery task to send a verification email to the user.

    This asynchronous task sends an email containing a verification link to the 
    user's email address. The email includes an HTML-formatted message with a 
    clickable verification link. This task is executed using Celery to ensure 
    non-blocking, background processing.

    Args:
        user_email (str): The email address of the user to whom the verification link should be sent.
        verification_link (str): The URL that the user can click to verify their account.

    Returns:
        None
    """
    html_message = format_html(
        'Hi {},<br><br>'
        'Please verify your email by clicking on the link below:<br>'
        '<a href="{}">Verify Email</a><br><br>'
        'Thank you!',
        user_email,
        verification_link
    )

    send_mail(
        'Verify your email',
        f'Use the following token to verify your email: {verification_link}',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
        html_message=html_message
    )
