#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from djangobmf.conf import settings
from djangobmf.models import BMFModel

from .workflows import TimesheetWorkflow


class TimesheetManager(models.Manager):

    def get_queryset(self):

        return super(TimesheetManager, self).get_queryset() \
            .annotate(end_count=models.Count('end')) \
            .order_by('end_count', '-end', 'summary') \
            .select_related('task', 'project', 'employee')

    def mytimesheets(self, request):
        return self.get_queryset().filter(
            employee=request.user.djangobmf.employee or -1,
        )


@python_2_unicode_compatible
class AbstractTimesheet(BMFModel):
    """
    """
    summary = models.CharField(_("Title"), max_length=255, null=True, blank=False, )
    description = models.TextField(_("Description"), null=True, blank=True, )
    start = models.DateTimeField(null=True, blank=False, default=now)
    end = models.DateTimeField(null=True, blank=True)
    billable = models.BooleanField(default=True)
    auto = models.BooleanField(default=False, editable=False)
    valid = models.BooleanField(default=False, editable=False)

    employee = models.ForeignKey(
        settings.CONTRIB_EMPLOYEE, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+"
    )

    project = models.ForeignKey(  # TODO: make optional
        settings.CONTRIB_PROJECT, null=True, blank=True, on_delete=models.SET_NULL,
    )

    task = models.ForeignKey(  # TODO: make optional
        settings.CONTRIB_TASK, null=True, blank=True, on_delete=models.SET_NULL,
    )

    objects = TimesheetManager()

    def clean(self):
        # overwrite the project with the goals project
        if self.task:
            self.project = self.task.project

    def get_project_queryset(self, qs):
        if self.task:
            return qs.filter(task=self.task)
        else:
            return qs

    def get_task_queryset(self, qs):
        if self.project:
            return qs.filter(project=self.project)
        else:
            return qs

    class Meta(BMFModel.Meta):  # only needed for abstract models
        verbose_name = _('Timesheet')
        verbose_name_plural = _('Timesheets')
        ordering = ['-end']
        abstract = True
        permissions = (
            ('can_manage', 'Can manage timesheets'),
        )
        swappable = "BMF_CONTRIB_TIMESHEET"

    def bmfget_customer(self):
        if self.project:
            return self.project.customer
        return None

    def bmfget_project(self):
        return self.project

    def __str__(self):
        return '%s' % (self.start)

    class BMFMeta:
        has_logging = True
        workflow = TimesheetWorkflow


class Timesheet(AbstractTimesheet):
    pass
