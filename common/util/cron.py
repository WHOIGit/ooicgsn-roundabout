import os
from django.core import management
from django.conf import settings
from django_cron import CronJobBase, Schedule

class DBBackupCronJob(CronJobBase):
    RUN_AT_TIMES = ['14:00', '1:15']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'ooi_parts.dbbackup_run'

    def do(self):
        management.call_command('dbbackup', clean=True)
