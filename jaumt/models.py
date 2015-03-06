import requests

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group, User


class RecipientList(models.Model):
    description = models.CharField(max_length=300)
    recipients = models.ManyToManyField(Group)

    def __str__(self):
        return self.description


class Website(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=140)
    enabled = models.BooleanField(default=False, blank=True)
    owner = models.ForeignKey(User)
    recipients_list = models.ManyToManyField(RecipientList)

    def __str__(self):
        return self.name


class Url(models.Model):
    OK = 0
    WARNING = 1
    ERROR = 2

    STATUS_CHOICES = (
        (OK, 'Ok'),
        (WARNING, 'Warning'),
        (ERROR, 'Error')
    )

    description = models.CharField(max_length=140)
    website = models.ForeignKey(Website, related_name='urls')
    url = models.URLField()
    hostname = models.URLField(null=True, blank=True)
    timeout = models.IntegerField(default=2000)
    response_ms_sla = models.IntegerField(default=200)
    no_cache = models.BooleanField(default=False, blank=True)
    match_text = models.CharField(max_length=100, null=True, blank=True)
    no_match_text = models.CharField(max_length=100, null=True, blank=True)
    recipients_list = models.ManyToManyField(RecipientList,
                                             blank=True,
                                             null=True)

    enabled = models.BooleanField(default=False, blank=True)

    # not editables
    current_status = models.IntegerField(choices=STATUS_CHOICES,
                                         default=OK, editable=False)
    current_status_code = models.IntegerField(null=True, editable=False)
    last_check = models.DateTimeField(null=True,
                                      editable=False,
                                      auto_now=True)

    last_check_ok = models.DateTimeField('Last OK',
                                         null=True,
                                         editable=False)

    last_check_warn = models.DateTimeField('Last WARNING',
                                           null=True,
                                           editable=False)

    last_check_error = models.DateTimeField('Last ERROR',
                                            null=True,
                                            editable=False)

    def __str__(self):
        return "{} - Last Check {} - {}. ".format(self.url, self.last_check,
                                                  self.current_status)

    def check_http(self):
        """ Ping the URL and get the status """
        response = requests.get(self.url)
        self.current_status_code = response.status_code

        if response.ok:
            if self.current_status == Url.ERROR:
                pass
                # send OK notification
            self.current_status = Url.OK
            self.last_check_ok = timezone.now()
        else:
            if self.current_status == Url.OK:
                self.current_status = Url.WARNING
                self.last_check_warn = timezone.now()

            elif self.current_status == Url.WARNING:
                self.current_status = Url.ERROR
                self.last_check_error = timezone.now()
                # send ERROR notification

        # send to graphite status_code, response_time, size, etc
        self.save()