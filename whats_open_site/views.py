from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.views.decorators.http import condition
from django.views.generic import ListView, DetailView

from .models import Facility, OpenTime, Category, Schedule 
from .api import export_data
from .serializers import  CategorySerializer, FacilitySerializer, ScheduleSerializer, OpenTimeSerializer

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response

import hashlib
import json


class FacilityListView(ListView):
    model = Facility
    queryset = Facility.objects.all()

class FacilityCategoryListView(ListView):
    model = Facility
    def get_queryset(self):
        return Facility.objects.filter(category=self.kwargs['category'])

class FacilityStatusListView(ListView):
    model = Facility
    def get_queryset(self):
        return Facility.objects.filter(on_campus=self.kwargs['on_campus'])
    
class FacilityDetailView(DetailView):
    model = Facility

class ScheduleDetailView(DetailView):
    model = Schedule

class OpenTimeDetailView(DetailView):
    model = OpenTime
"""
class CategoryListView(ListView):
    model = Categories
"""


def facility_grid(request):
    """Display the facilities in a grid. Main page."""
    if 'sort' in request.GET:
        if request.GET['sort'] == 'location':
            # Display the grid by location (instead of listing alphabetically)
            pass  # Not implemented yet
    return render_to_response('facility_grid.html', 
            context_instance=RequestContext(request))

def gen_etag(request):
    return hashlib.sha1(str(OpenTime.objects.all())).hexdigest()

def gen_last_modified(request):
    return BaseModel.objects.all().order_by('-last_modified')[0].last_modified


@condition(etag_func=gen_etag, last_modified_func=gen_last_modified)
def ajax_schedule_data(request):
    # Wrapping up in an object to avoid possible CSRF attack on top-level
    # arrays in JSON objects
    return HttpResponse(json.dumps({'data': export_data()}, indent=4),
            content_type="application/json")

