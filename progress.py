import requests
import json
import sys
from constants import *
from datetime import datetime
from statistics import median_high, variance, mean, stdev

COMPARATION_IS = "="
COMPARATION_IS_NOT = "!"

DATE_COMPARATION_IS = "="
DATE_COMPARATION_GE = ">="
DATE_COMPARATION_LE = "<="
DATE_COMPARATION_LESS_THAN_DAYS_AGO = ">t-"
DATE_COMPARATION_MORE_THAN_DAYS_AGO = "<t-"
DATE_COMPARATION_IN_THE_PAST = "><t-"
DATE_COMPARATION_DAYS_AGO = "t-"
DATE_COMPARATION_BETWEEN = "><"
DATE_COMPARATION_TODAY = "t"
DATE_COMPARATION_YESTERDAY = "ld"
DATE_COMPARATION_THIS_WEEK = "w"
DATE_COMPARATION_LAST_WEEK = "lw"
DATE_COMPARATION_LAST_2_WEEKS = "l2w"
DATE_COMPARATION_THIS_MONTH = "m"
DATE_COMPARATION_LAST_MONTH = "lm"
DATE_COMPARATION_THIS_YEAR = "y"

DATE_CREATED = "created_on"
DATE_UPDATED = "updated_on"
DATE_CLOSED = "closed_on"
DATE_START = "start_date"

PRIORITIES = [ "immediate", "urgent", "high", "normal", "low" ]

INCLUDE_CHILDREN = "children"
INCLUDE_ATTACHMENTS = "attachments"
INCLUDE_RELATIONS = "relations"
INCLUDE_CHANGESETS = "changesets"
INCLUDE_JOURNALS = "journals"
INCLUTE_WATCHERS = "watchers"
INCLUDE_ALLOWED_STATUSES = "allowed_statuses"
INCLUDE_ALL = [INCLUDE_CHILDREN, INCLUDE_ATTACHMENTS, INCLUDE_RELATIONS, INCLUDE_CHANGESETS, INCLUDE_JOURNALS, INCLUTE_WATCHERS, INCLUDE_ALLOWED_STATUSES]

def trunc_datetime(someDate):
    return someDate.replace(hour=0, minute=0, second=0, microsecond=0)

def prepare_list_for_json(arr):
    l=[]
    for i in arr:
        if isinstance(i, Issue):
            l.append(i.getData())
        else:
            l.append(i)

    return l

def status_to_text(value):
    if value == STATUS_NEW:
        return "new"
    elif value == STATUS_WORKABLE:
        return "workable"
    elif value == STATUS_IN_PROGRESS:
        return "in progress"
    elif value == STATUS_BLOCKED:
        return "blocked"
    elif value == STATUS_RESOLVED:
        return "resolved"
    elif value == STATUS_FEEDBACK:
        return "feedback"
    elif value == STATUS_CLOSED:
        return "closed"
    elif value == STATUS_REJECTED:
        return "rejected"
    else:
        return "unknown"

def priority_from_text(text):
    if text == "immediate":
        return PRIORITY_IMMEDIATE
    elif text == "urgent":
        return PRIORITY_URGENT
    elif text == "high":
        return PRIORITY_HIGH
    elif text == "normal":
        return PRIORITY_NORMAL
    elif text == "low":
        return PRIORITY_LOW
    else:
        sys.stderr.write("Invalid priority. Options immediate, urgent, high, normal, low\n")
        exit(2)

def _variance(values):
    if len(values) < 2:
        return 0
    else:
        return variance(values)

def _stdev(values):
    if len(values) < 2:
        return 0
    else:
        return stdev(values)

class Issues:
    def __init__(self, data):
        self.data = data

        self.issues = []
        if "issues" in data:
            for item in data["issues"]:
                self.issues.append(Issue(item))

    def __iter__(self):
        return self.issues

    def __len__(self):
        return self.issues.count()

    def __str__(self):
        return json.dumps(prepare_list_for_json(self.issues))

    def count(self):
        return self.data["total_count"]

    def limit(self):
        return self.data["limit"]

    def reloadJournals(self, progress):
        for issue in self.issues:
            issue.reloadJournals(progress)

    def snapshot(self, date):
        arr = []
        for issue in self.issues:
            issueToAdd = issue.snapshot(date)
            arr.append(issueToAdd)

        res = Issues([])
        res.issues = arr
        return res

    def stats_status(self):
        stats = {}

        for status in STATUS_ALL:
            stats[status] = 0
            stats[f"{status}_ids"] = []

        for issue in self.issues:
            issue_status = issue.getStatusText()
            if issue_status in stats:
                stats[issue_status] = stats[issue_status] + 1
                stats[f"{issue_status}_ids"].append(issue.id())

        return stats

    def stats_aging(self):
        result = {}

        for status in STATUS_ALL:
            result[status] = {"count": 0, "sum": 0, "avg": 0, "values": []}

        for issue in self.issues:
            aging = issue.stats_aging()

            for status in STATUS_ALL:
                if aging[status] != 0:
                    result[status]["sum"] = result[status]["sum"] + aging[status]
                    result[status]["count"] = result[status]["count"] + 1
                    result[status]["values"].append(aging[status])

        for status in STATUS_ALL:
            if result[status]["count"] >0:
                result[status]["avg"] = mean(result[status]["values"])
                result[status]["med"] = median_high(result[status]["values"])
                result[status]["stdev"] = _stdev(result[status]["values"])
                result[status]["variance"] = _variance(result[status]["values"])
                result[status].pop("values")

        return result

class Issue:
    def __init__(self, data):
        self.raw = data

        if "issue" in data:
            self.data = data["issue"]
        else:
            self.data = data

        self.data["description"] = ""

        if "journals" in self.data:
            self.journals = []
            if "journals" in self.data:
                for journal in self.data["journals"]:
                    self.journals.append(Journal(journal))

    def reloadJournals(self, progress):
        newData = progress.issue(self.data["id"], [progress.include(INCLUDE_JOURNALS)])
        self.raw = newData.raw
        self.journals = newData.journals

    def id(self):
        return self.data["id"]

    def getData(self):
        return self.data

    def createOn(self):
        return trunc_datetime(datetime.strptime(self.data["created_on"], '%Y-%m-%dT%H:%M:%SZ'))

    def createOnFull(self):
        return datetime.strptime(self.data["created_on"], '%Y-%m-%dT%H:%M:%SZ')

    def closedOn(self):
        return trunc_datetime(datetime.strptime(self.data["closed_on"], '%Y-%m-%dT%H:%M:%SZ'))

    def closedOnFull(self):
        return datetime.strptime(self.data["closed_on"], '%Y-%m-%dT%H:%M:%SZ')

    def __str__(self):
        return json.dumps(self.data)

    def getStatusChanges(self):
        result = []
        for journal in self.journals:
            if journal.isStatus():
                result.append(journal)

        return result

    def getStatusByDate(self, date):
        date = trunc_datetime(date)
        current = None
        for journal in self.journals:
            if journal.isStatus():
                if date >= journal.date():
                    current = journal

        if current is None:
            return 0
        else:
            return int(current.status())

    def status(self):
        return self.data["status"]["id"]

    def snapshot(self, date):
        res = Issue(self.data)
        res.journals = self.journals
        status = self.getStatusByDate(date)

        res.data["status"] = { "id" : status, "name": status_to_text(status)}

        return res

    def stats_aging(self):
        ret={}
        for status in STATUS_ALL:
            ret[status] = 0

        changeList = self.getStatusChanges()
        currentStatus = STATUS_NEW
        startDate = self.createOnFull()

        for change in changeList:
            newStaus = change.status()
            endDate = change.dateFull()
            elapsed = (endDate - startDate).seconds / 3600

            status = status_to_text(currentStatus)
            if status not in ret:
                ret[status] = elapsed
            else:
                ret[status] = ret[status] + elapsed

            currentStatus = newStaus
            startDate = endDate

        if currentStatus != STATUS_CLOSED:
            today = datetime.today()
            status = status_to_text(currentStatus)
            elapsed = (today - startDate).seconds / 3600
            if status not in ret:
                ret[status] = elapsed
            else:
                ret[status] = ret[status] + elapsed

        return ret

    def getStatus(self):
        return self.data["status"]["id"]
 
    def getStatusText(self):
        return self.data["status"]["name"]

class Journal:
    def __init__(self, data):
        self.data = data
        self.data["notes"] = ""

    def __str__(self):
        return json.dumps(self.data)

    def isStatus(self):
        return self.status() is not None

    def status(self):
        if "details" in self.data and len(self.data["details"]) >0:
            for i in  self.data["details"]:
                if i["name"] == "status_id":
                    return int(i["new_value"])
        return None

    def date(self):
        return trunc_datetime(datetime.strptime(self.data["created_on"], '%Y-%m-%dT%H:%M:%SZ'))

    def dateFull(self):
        return datetime.strptime(self.data["created_on"], '%Y-%m-%dT%H:%M:%SZ')


class Progress:
    def __init__(self, baseUrl, key):
        self.baseUrl = baseUrl
        self.key = key

    def rawQuery(self, url):
        result = requests.get(url, headers={'X-Redmine-API-Key': self.key})
        return result.json()

    def query(self, url, filters = []):
        query = f"{self.baseUrl}{url}?utf8=✓&set_filter=1"

        for filter in filters:
            query = query + "&" + filter

        #sys.stderr.write(query)

        return self.rawQuery(query)

    def prepare_filter(self, key, values, operator):
        if isinstance(values, list):
            str = f"f[]={key}&op[{key}]={operator}"
            for value in values:
                str = str + f"&v[{key}][]={value}"
            return str
        else :
            return self.prepare_filter(key, [values], operator)

    def filter_status(self, values, operator=COMPARATION_IS):
        return self.prepare_filter("status_id", values, operator)

    def filter_tracker(self, values, operator=COMPARATION_IS):
        return self.prepare_filter("tracker_id", values, operator)

    def filter_date(self, key, date, operator):
        return self.prepare_filter(key, [date], operator)

    def filter_date_between(self, key, date1, date2):
        return self.prepare_filter(key, [date1, date2], DATE_COMPARATION_BETWEEN)

    def filter_tag(self, values, operator=COMPARATION_IS):
        return self.prepare_filter("issue_tags", values, operator)

    def filter_priority(self, values, operator=COMPARATION_IS):
        return self.prepare_filter("priority_id", values, operator)

    def include(self, values):
        if isinstance(values, list):
            return "include=" + ",".join(values)
        else:
            return self.include([values])

    def limit(self, value):
        return f"limit={value}"

    def issues(self, project, filters = []):
        return Issues(self.query(f"/projects/{project}/issues.json", filters))

    def issue(self, id, includes):
        return Issue(self.query(f"/issues/{id}.json", includes))
