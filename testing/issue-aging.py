import sys
sys.path.append("..")

from progress import *
from config import *
from constants import *

issueId = 114598
dateStr = "2022-07-26"

progress = Progress( PROGRESS_URL, PROGRESS_KEY)

issue = progress.issue(issueId, [
    progress.include(INCLUDE_JOURNALS)
    ])

print("Status changes")
for j in issue.getStatusChanges():
    print(j)

print("Aging (in days)")
print(issue.stats_aging())