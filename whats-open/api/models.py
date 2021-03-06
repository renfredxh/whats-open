#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
api/models.py

Define the objects that will be stored in the database and later served through
the API.

https://docs.djangoproject.com/en/1.11/topics/db/models/
"""
# Python Imports
import datetime

# Django Imports
from django.db import models
from django.contrib.gis.db.models import PointField
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone

# Other Imports
from model_utils.models import TimeStampedModel
from autoslug import AutoSlugField
from taggit.managers import TaggableManager


class Category(TimeStampedModel):
    """
    Represents the "category" that a Facility falls under. A Category is a
    grouping of Facilities that serve a common/similar purpose.

    ex.
    - Dining
    - Gyms
    - Study areas (Libraries, The Ridge, JC, etc)
    """

    # The name of the category
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        # Sort by name in admin view.
        ordering = ["name"]

    def __str__(self):
        """
        String representation of a Category object.
        """
        return self.name


class Location(TimeStampedModel):
    """
    Represents a specific location that a Facility can be found.
    """

    CAMPUS_LOCATIONS = (
        ("front royal", "Front Royal"),
        ("prince william", "Prince William County Science and Technology"),
        ("fairfax", "Fairfax"),
        ("arlington", "Arlington"),
    )
    # The building that the facility is located in (on campus).
    building = models.CharField(max_length=100)
    friendly_building = models.CharField(
        "Building Abbreviation",
        help_text="Example: Exploratory Hall becomes EXPL",
        blank=True,
        max_length=10,
    )
    # The physical address of the facility.
    address = models.CharField(max_length=100)
    campus_region = models.CharField(choices=CAMPUS_LOCATIONS, max_length=100)
    # Boolean for whether or not the location is "on campus" or not.
    on_campus = models.BooleanField(default=True)
    # A GeoJson coordinate pair that represents the physical location
    coordinate_location = PointField()

    class Meta:
        verbose_name = "location"
        verbose_name_plural = "locations"

    def __str__(self):
        """
        String representation of a Location object.
        """
        return "%s on %s Campus" % (self.building, self.campus_region.title())


class Facility(TimeStampedModel):
    """
    Represents a specific facility location. A Facility is some type of
    establishment that has a schedule of open hours and a location that serves
    a specific purpose that can be categorized.
    """

    # The name of the Facility
    facility_name = models.CharField(max_length=100)
    # Instead of id
    slug = AutoSlugField(populate_from="facility_name", unique=True)

    # The category that this facility can be grouped with
    facility_category = models.ForeignKey(
        "Category", related_name="categories", on_delete=models.CASCADE
    )
    # The location object that relates to this facility
    facility_location = models.ForeignKey(
        "Location", related_name="facilities", on_delete=models.CASCADE
    )

    # A note that can be left on a Facility to provide some additional
    # information.
    note = models.TextField(
        "Facility Note",
        blank=True,
        help_text="Additional information that is sent with this Facility.",
    )

    # A link to the logo image for this Facility
    logo = models.URLField(
        "Logo URL",
        blank=True,
        default="https://wopen-cdn.dhaynes.xyz/default.png",
        help_text="The absolute URL to the logo image for this Facility.",
    )

    # The User(s) that claim ownership over this facility
    owners = models.ManyToManyField(User)

    # The schedule that is defaulted to if no special schedule is in effect
    main_schedule = models.ForeignKey(
        "Schedule", related_name="facility_main", on_delete=models.CASCADE
    )
    # A schedule that has a specific start and end date
    special_schedules = models.ManyToManyField(
        "Schedule",
        related_name="facility_special",
        blank=True,
        help_text="This schedule will come into effect only for its specified duration.",
    )

    # URL, if it exists, to the Tapingo page that is associated with this
    # facility
    tapingo_url = models.URLField(
        blank=True,
        validators=[
            RegexValidator(
                regex="^https:\/\/www.tapingo.com\/",
                message="The link is not a valid tapingo link. Example: https://www.tapingo.com/order/restaurant/starbucks-gmu-johnson/",
                code="invalid_tapingo_url",
            )
        ],
    )

    # Phone number for a location if provided. Accept both ###-###-#### or
    # without dashes
    phone_number = models.CharField(
        blank=True,
        max_length=18,
        validators=[
            RegexValidator(
                regex="^\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})$",
                message="Invalid phone number",
                code="invalid_phone_number",
            )
        ],
    )

    # A comma seperate list of words that neatly and aptly describe the product
    # that this facility produces. (ex. for Taco Bell: mexican, taco, cheap)
    # These words are not shown to the use but are rather used in search.
    facility_product_tags = TaggableManager(
        related_name="product_tags",
        help_text="A comma seperate list of words that neatly and aptly describe the product that this facility produces. These words are not shown to the use but are rather used in search.",
    )

    # Tag a Facility to be shown on the ShopMason
    # What's Open sites.
    FACILITY_CLASSES = (("shopmason", "shopMason Facility"),)
    facility_classifier = models.CharField(
        choices=FACILITY_CLASSES,
        help_text="Tag this facility to be shown on the ShopMason What's Open sites.",
        max_length=100,
        blank=True,
    )

    def is_open(self):
        """
        Return true if this facility is currently open.

        First checks any valid special schedules and then checks the main,
        default, schedule.
        """
        today = timezone.now()
        # Check special schedules first
        for schedule in self.special_schedules.all():
            # Special schedules must have valid_start and valid_end set
            if schedule.valid_start and schedule.valid_end:
                if schedule.valid_start <= today <= schedule.valid_end:
                    return schedule.is_open_now()

        # If no special schedule is in effect then check the main_schedule
        return self.main_schedule.is_open_now()

    class Meta:
        verbose_name = "facility"
        verbose_name_plural = "facilities"
        # Sort by name in admin view
        ordering = ["facility_name"]

    def __str__(self):
        """
        String representation of a Facility object.
        """
        return self.facility_name


class Schedule(TimeStampedModel):
    """
    A period of time between two dates that represents the beginning and end of
    a "schedule" or rather, a collection of open times for a facility.
    """

    # The name of the schedule
    name = models.CharField(max_length=100)

    # The start date of the schedule
    # (inclusive)
    valid_start = models.DateTimeField(
        "Start Date",
        null=True,
        blank=True,
        help_text="Date & time that this schedule goes into effect",
    )
    # The end date of the schedule
    # (inclusive)
    valid_end = models.DateTimeField(
        "End Date",
        null=True,
        blank=True,
        help_text="Last date & time that this schedule is in effect",
    )

    # Boolean for if this schedule is 24 hours
    twenty_four_hours = models.BooleanField(
        "24 hour schedule?",
        blank=True,
        default=False,
        help_text="Toggle to True if the Facility is open 24 hours. You do not need to specify any Open Times, it will always be displayed as open.",
    )

    def is_open_now(self):
        """
        Return true if this schedule is open right now.
        """
        # If the schedule is a 24 hour one, then it's open.
        if self.twenty_four_hours:
            return True
        else:
            # Loop through all the open times that correspond to this schedule
            for open_time in OpenTime.objects.filter(schedule=self):
                if open_time.is_open_now():
                    return True
            # Closed (all open times are not open)
            return False

    class Meta:
        # Sort by name in admin view
        ordering = ["name"]

    def __str__(self):
        """
        String representation of a Schedule object.
        """
        return self.name


class OpenTime(TimeStampedModel):
    """
    Represents a time period when a Facility is open.

    Monday = 0, Sunday = 6.
    """

    # Define integer constants to represent days of the week
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    # Tuple that ties a day of the week with an integer representation
    DAY_CHOICES = (
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    )

    # The schedule that this period of open time is a part of
    schedule = models.ForeignKey(
        "Schedule", related_name="open_times", on_delete=models.CASCADE
    )

    # The day that the open time begins on
    start_day = models.IntegerField(default=0, choices=DAY_CHOICES)
    # The day that the open time ends on
    end_day = models.IntegerField(default=0, choices=DAY_CHOICES)

    # The time of day that the open time begins at
    start_time = models.TimeField()
    # The time of day that the open time ends
    end_time = models.TimeField()

    def is_open_now(self):
        """
        Return true if the current time is this OpenTime's range.
        """
        # Get the current datetime
        today = datetime.datetime.today()

        # Check that the start occurs before the end
        if self.start_day <= self.end_day:
            # If today is the start_day
            if self.start_day == today.weekday():
                # If the start_time has not occurred
                if self.start_time > today.time():
                    # Closed
                    return False
            # If the start_day has not occurred
            elif self.start_day > today.weekday():
                # Closed
                return False
            # If the end_day is today
            if self.end_day == today.weekday():
                # If the end_time has already occurred
                if self.end_time < today.time():
                    # Closed
                    return False
            # If the end_day has already occurred
            elif self.end_day < today.weekday():
                # Closed
                return False
        # The start_day > end_day
        else:
            # If today is the start_day
            if self.start_day == today.weekday():
                # If the start_time has not occurred
                if self.start_time > today.time():
                    # Closed
                    return False
            # If the end_day is today
            if self.end_day == today.weekday():
                # If the end_time has already occurred
                if self.end_time < today.time():
                    # Closed
                    return False
            # If the current date takes place after the end_date but before
            # start_day
            if self.end_day < today.weekday() < self.start_day:
                # Closed
                return False
        # All checks passed, it's open
        return True

    def __str__(self):
        """
        String representation of a OpenTime object.
        """
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return "%s %s to %s %s" % (
            weekdays[self.start_day],
            self.start_time.strftime("%H:%M:%S"),
            # to
            weekdays[self.end_day],
            self.end_time.strftime("%H:%M:%S"),
        )


class Alert(TimeStampedModel):
    """
    Some type of notification that is displayed to clients that conveys a
    message. Past examples include: random closings, modified schedules being
    in effect, election reminder, advertising for other SRCT projects.

    Alerts last for a period of time until the information is no longer dank.
    """

    # Define string constants to represent urgency tag levels
    INFO = "info"  # SRCT announcements
    MINOR = "minor"  # Holiday hours are in effect
    MAJOR = "major"  # The hungry patriot is closed today
    EMERGENCY = "emergency"  # Extreme weather

    # Tuple that ties a urgency tag with a string representation
    URGENCY_CHOICES = (
        (INFO, "Advertising / Announcement"),
        (MINOR, "Expected Hours Change"),
        (MAJOR, "(Small Scale) Unexpected Hours Change"),
        (EMERGENCY, "(University Wide) Unexpected Hours Change"),
    )

    # The urgency tag for this Alert
    urgency_tag = models.CharField(
        max_length=10, default="Info", choices=URGENCY_CHOICES
    )

    # The text that is displayed that describes the Alert
    subject = models.CharField(max_length=130)
    body = models.TextField()
    url = models.URLField("Reference URL", max_length=200, blank=True)

    # The date + time that the alert will be start being served
    start_datetime = models.DateTimeField()

    # The date + time that the alert will stop being served
    end_datetime = models.DateTimeField()

    def is_active(self):
        """
        Check if the current Alert object is active (Alert-able).
        """
        # Get the current datetime
        now = timezone.now()
        return self.start_datetime < now < self.end_datetime

    def __str__(self):
        """
        String representation of an Alert object.
        """
        return "{0} \n {1} \n {2}".format(self.subject, self.body, self.url)
