from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler

class Command(BaseCommand):
    help = 'List all scheduled APScheduler jobs'

    def handle(self, *args, **kwargs):
        # Retrieve the scheduler instance. 
        # In a real application, you'd want to use a singleton or similar pattern to access the running scheduler.
        scheduler = BackgroundScheduler()
        # scheduler.start()
        self.list_scheduled_jobs(scheduler)

    def list_scheduled_jobs(self, scheduler):
        jobs = scheduler.get_jobs()
        for job in jobs:
            self.stdout.write(f"Job ID: {job.id}")
            self.stdout.write(f"Job Name: {job.name}")
            self.stdout.write(f"Job Trigger: {job.trigger}")
            self.stdout.write(f"Job Next Run Time: {job.next_run_time}")
            self.stdout.write(f"Job Job Store: {job.jobstore}")
            self.stdout.write(f"Job Args: {job.args}")
            self.stdout.write(f"Job Kwargs: {job.kwargs}")
            self.stdout.write("---")
