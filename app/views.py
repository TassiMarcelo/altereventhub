import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Comment, Event
from .forms import CommentForm

from .models import Event, User


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )

#crear comentario
@login_required
def add_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.event = event
            comment.save()
            messages.success(request, '¡Comentario publicado!')
            return redirect('event_detail', id=event.id)
    else:
        form = CommentForm()
    return render(request, 'comments/add_comment.html', {'form': form, 'event': event})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, user=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Comentario actualizado!')
            return redirect('event_detail', id=comment.event.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'comments/edit_comment.html', {'form': form, 'comment': comment})



@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.user and request.user != comment.event.organizer:
        return HttpResponseForbidden()

    comment.delete()

    # Redirigir a la URL indicada en 'next', si existe
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    # Si no hay 'next', redirigir al detalle del evento como fallback
    return redirect('event_detail', id=comment.event.id)


@login_required
def organizer_comments(request):
    if not request.user.is_organizer:
        return redirect('events')
    
    # Obtener solo los eventos creados por este organizador
    organizer_events = Event.objects.filter(organizer=request.user)
    
    # Obtener todos los comentarios de esos eventos
    comments = Comment.objects.filter(event__in=organizer_events).select_related('user', 'event').order_by('-created_at')
    
    return render(request, 'comments/organizer_comments.html', {
        'comments': comments
    })
    
    
def view_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    return render(request, 'comments/view_comment.html', {'comment': comment})