from django.conf.urls import patterns, url

from . import views

from rest_framework.routers import DefaultRouter

#router = DefaultRouter()


urlpatterns = patterns('whats_open_sites.views',
    url(r'^(?:ajax|api)/schedule/', 'ajax_schedule_data', name='schedule_data'),
    url(r'^$', 'facility_grid', name='facility_grid'),

    #facilities open urls
    url(r'^facilities/$', FacilitiesListView.as_view(), name='faciliites-list'),
    url(r'^facilities/(?P<category>/$', FacilitiesListView.as_view(), name='facilities-list-by-cat'),
    url(r'^facilities/(?P<slug>/$', FacilitiesDetailView.as_view(), name='facilities-detail'),
    url(r'^facilities/(?P<on_campus>/$', FaciltiesListView.as_view(), name-'facilities-list-by-status'),

    #schedules urls
    url(r'^schedule/(?P<id>/$', ScheduleDetailView.as_view(), name='schedule-detail'),

    #opentime urls
    url(r'^open-time/(?P<id>/$', OpenTimeDetailView.as_view(), name='open-time-detail'),
)

