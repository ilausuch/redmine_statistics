from datetime import timedelta
import sys
sys.path.append("..")

from progress import *
from config import *
from constants import *

project = "containers"
dateStr = "2022-10-10"

progress = Progress( PROGRESS_URL, PROGRESS_KEY)

issues = progress.issues(project, [
    progress.filter_tracker(TRACKER_ACTION),
    progress.limit(1000),
    progress.filter_date(DATE_UPDATED, 200, DATE_COMPARATION_LESS_THAN_DAYS_AGO)
])

issues.reloadJournals(progress)

print(issues.stats_aging())