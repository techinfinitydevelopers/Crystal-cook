from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactSubmission


def index_redirect(request):
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect('/')


def about(request):
    return render(request, 'about.html')


def career(request):
    return render(request, 'career.html')


def privacy(request):
    return render(request, 'privacy.html')


def terms(request):
    return render(request, 'terms.html')


def contact(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        errors = {}
        if not full_name:
            errors['full_name'] = 'Name is required.'
        if not email or '@' not in email:
            errors['email'] = 'Valid email is required.'
        if not subject:
            errors['subject'] = 'Subject is required.'
        if not message:
            errors['message'] = 'Message is required.'

        if not errors:
            ContactSubmission.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
            )
            return render(request, 'contact.html', {'success': True})

        return render(request, 'contact.html', {'errors': errors, 'form_data': request.POST})

    return render(request, 'contact.html')
