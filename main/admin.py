from django.contrib import admin
from . import models


@admin.register(models.Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('ip', 'last_visit', 'user_agent', 'session_key')
    search_fields = ('ip', 'user_agent', 'session_key')
    list_filter = ('last_visit',)
    readonly_fields = ('ip', 'last_visit', 'user_agent', 'session_key')
