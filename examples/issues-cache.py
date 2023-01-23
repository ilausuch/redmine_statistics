import sys
sys.path.append("..")

from SQLiteCache import SQLiteCache
from constants import *
from config import *
from progress import *
from datetime import timedelta



project = "containers"

progress = Progress(PROGRESS_URL, PROGRESS_KEY)
cache = SQLiteCache("./progress.db", True)
cache.setup()

issues = progress.issues(project, [
    progress.filter_tracker(TRACKER_ACTION),
    progress.filter_date(
        DATE_CREATED, 10, DATE_COMPARATION_LESS_THAN_DAYS_AGO),
    progress.limit(500)
])

issues.reload_journals(progress)
issues.store(cache)
issues2 = cache.restore_all_issues()
print(issues2)
