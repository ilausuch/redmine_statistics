import sys
sys.path.append("..")

from constants import *
from config import *
from progress import *
from datetime import timedelta


project = "containers"
dateStr = "2022-10-10"

progress = Progress(PROGRESS_URL, PROGRESS_KEY)

issues = progress.issues(project, [
    progress.filter_tracker(TRACKER_ACTION),
    progress.limit(1000),
    progress.filter_date(
        DATE_UPDATED, 200, DATE_COMPARATION_LESS_THAN_DAYS_AGO)
])

issues.reload_journals(progress)

print(issues.stats_aging())
