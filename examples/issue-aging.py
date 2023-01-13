import sys
sys.path.append("..")

from constants import *
from config import *
from progress import *

issueId = 114598
dateStr = "2022-07-26"

progress = Progress(PROGRESS_URL, PROGRESS_KEY)

issue = progress.issue(issueId, [
    progress.include(INCLUDE_JOURNALS)
])

print("Status changes")
for j in issue.state_changes:
    print(j)

print("Aging (in days)")
print(issue.stats_aging())

print("Plain values")
print(issue.plain_values)
