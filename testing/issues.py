'''
Example: Get the number of issues
'''

from datetime import timedelta
import sys
sys.path.append("..")

from progress import *
from config import *
from constants import *

project = "qe-yast"

progress = Progress( PROGRESS_URL, PROGRESS_KEY)

issues = progress.issues(project, [
    progress.filter_tracker(TRACKER_ACTION),
    progress.limit(100),
    progress.filter_status(STATUS_IN_PROGRESS)
])

print(f"Total issues: {issues.count()}")

issues.reloadJournals(progress)
print(issues.stats_aging())
