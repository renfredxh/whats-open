from django.contrib import admin
from website.models import Facility, Schedule, OpenTime


class OpenTimeInline(admin.TabularInline):
    model = OpenTime
    fk_name = 'schedule'


class ScheduleAdmin(admin.ModelAdmin):
    inlines = [OpenTimeInline, ]


admin.site.register(Facility)
admin.site.register(Schedule, ScheduleAdmin)