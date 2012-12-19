#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from alerts.models import *

class NotificationAdmin(admin.ModelAdmin):
    model = Notification

class NotificationCommentAdmin(admin.ModelAdmin):
    model = NotificationComment

class NotificationVisibilityAdmin(admin.ModelAdmin):
    model = NotificationVisibility

admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationComment, NotificationCommentAdmin)
admin.site.register(NotificationVisibility, NotificationVisibilityAdmin)

