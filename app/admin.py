from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event', 'created_at')
    list_filter = ('event', 'user')
    search_fields = ('title', 'text')