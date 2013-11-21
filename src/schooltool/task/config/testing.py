# SchoolTool web server access to the celery results

from schooltool.task.config.worker_default import *

CELERY_RESULT_BACKEND = None
CELERY_ALWAYS_EAGER = True
