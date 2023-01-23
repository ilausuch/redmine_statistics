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

print("Issue")
print(issue)

print("Status changes")
for j in issue.statusChanges():
    print(j)

print(f"Get status bu date {dateStr}")
date = datetime.strptime(dateStr, "%Y-%m-%d")
status = issue.get_status_by_date(date)
print(f"On {date} the status is {status}")
