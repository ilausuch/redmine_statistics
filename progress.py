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

PRIORITIES = ["immediate", "urgent", "high", "normal", "low"]

INCLUDE_CHILDREN = "children"
INCLUDE_ATTACHMENTS = "attachments"
INCLUDE_RELATIONS = "relations"
INCLUDE_CHANGESETS = "changesets"
INCLUDE_JOURNALS = "journals"
INCLUTE_WATCHERS = "watchers"
INCLUDE_ALLOWED_STATUSES = "allowed_statuses"
INCLUDE_ALL = [INCLUDE_CHILDREN, INCLUDE_ATTACHMENTS, INCLUDE_RELATIONS,
               INCLUDE_CHANGESETS, INCLUDE_JOURNALS, INCLUTE_WATCHERS, INCLUDE_ALLOWED_STATUSES]

EPOCH = datetime(1970, 1, 1, 0, 0, 0)


def trunc_datetime(someDate):
    return someDate.replace(hour=0, minute=0, second=0, microsecond=0)


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
        sys.stderr.write(
            "Invalid priority. Options immediate, urgent, high, normal, low\n")
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


def tree_to_plain(obj, separator=".", prefix=""):
    res = {}
    for field in obj.keys():
        value = obj[field]
        if type(value) is dict:
            res2 = tree_to_plain(
                value, separator, f"{prefix}{field}{separator}")
            for field2 in res2.keys():
                res[field2] = res2[field2]

        elif type(value) in (tuple, list):
            raise Exception("The arrays are not implemented")
        else:
            res[f"{prefix}{field}"] = value

    return res


def plain_to_tree(data, separator="."):
    res = {}
    for field in data.keys():
        value = data[field]
        levels = field.split(separator)
        pointer = res
        for i in range(0, len(levels)):
            level = levels[i]
            if i == len(levels) - 1:
                pointer[level] = value
            else:
                if levels[i] not in pointer:
                    pointer[level] = {}
                pointer = pointer[level]

    return res


def parse_datetime(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')


def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d')


def datetime_to_seconds(value):
    return (datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ') - EPOCH).total_seconds()


def date_to_seconds(value):
    return (datetime.strptime(value, '%Y-%m-%d') - EPOCH).total_seconds()


def datetime_from_seconds(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%dT%H:%M:%SZ')


def date_from_seconds(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d')


class Issues:
    def __init__(self, data=[]):
        self.data = data

        if "issues" in data:
            self.issues = []
            for item in data["issues"]:
                self.issues.append(Issue(item))
        else:
            self.issues = data

    def __iter__(self):
        return self.issues

    def __len__(self):
        return len(self.issues)

    def __str__(self):
        issues_str = '['
        for issue in self.issues:
            issues_str += f"'{issue}'"
        issues_str += ']'
        return issues_str

    def count(self):
        return self.data["total_count"]

    def limit(self):
        return self.data["limit"]

    def reload_journals(self, progress):
        for issue in self.issues:
            issue.reload_journals(progress)

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
            issue_status = issue.status_text()
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
                    result[status]["sum"] = result[status]["sum"] + \
                        aging[status]
                    result[status]["count"] = result[status]["count"] + 1
                    result[status]["values"].append(aging[status])

        for status in STATUS_ALL:
            if result[status]["count"] > 0:
                result[status]["avg"] = mean(result[status]["values"])
                result[status]["med"] = median_high(result[status]["values"])
                result[status]["stdev"] = _stdev(result[status]["values"])
                result[status]["variance"] = _variance(
                    result[status]["values"])
                result[status].pop("values")

        return result

    def store(self, cache):
        for issue in self.issues:
            issue.store(cache, False)

        cache.commit()

    def restore(self, cache):
        cache.restore_all_issues()


class Issue:
    def __init__(self, data):
        self.raw = data
        self.journals = None
        self.state_changes = None

        if "issue" in data:
            self.data = data["issue"]
        else:
            self.data = data

        self.data["description"] = ""

        if "journals" in self.data:
            self.journals = []
            if "journals" in self.data:
                for journal in self.data["journals"]:
                    self.journals.append(Journal(journal, self))
            self._process_journals()

            self.data["journals"] = None

        self.plain_values = tree_to_plain(self.data)

    def reload_journals(self, progress):
        newData = progress.issue(
            self.data["id"], [progress.include(INCLUDE_JOURNALS)])
        self.raw = newData.raw
        self.journals = newData.journals
        self._process_journals()

    def id(self):
        return self.data["id"]

    def project_id(self):
        return self.data["project"]["id"]

    def get_data(self):
        data = self.data.copy()
        data.update(
            {"state_changes": self.state_changes})
        return data

    def __str__(self):
        return self.data

    def create_on(self):
        return parse_datetime(self.data["created_on"])

    def create_on_date(self):
        return trunc_datetime(self.create_on)

    def closed_on(self):
        return parse_datetime(self.data["closed_on"])

    def closed_on_date(self):
        return trunc_datetime(self.closed_on())

    def __str__(self):
        return json.dumps(self.get_data())

    def get_status_by_date(self, date):
        date = trunc_datetime(date)
        current = None
        for journal in self.journals:
            if journal.is_status():
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
        status = self.get_status_by_date(date)

        res.data["status"] = {"id": status, "name": status_to_text(status)}

        return res

    def stats_aging(self):
        ret = {}
        for status in STATUS_ALL:
            ret[status] = 0

        currentStatus = STATUS_NEW
        startDate = self.create_on()

        for change in self.state_changes:
            newStaus = change.status()
            endDate = change.create_on_date()
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

    def status(self):
        return self.data["status"]["id"]

    def status_text(self):
        return self.data["status"]["name"]

    def store(self, cache, auto_commit=True):
        cache.store_issue(self, auto_commit)

    def _process_journals(self):
        if self.journals != None:
            self.state_changes = []
            for journal in self.journals:
                for state in journal.data["details"]:
                    if state["property"] == "attr" and state["name"] == "status_id":
                        self.state_changes.append(State(state, journal, self))


class Journal:
    def __init__(self, data, issue):
        self.data = data
        self.issue = issue
        self.data["notes"] = ""

    def __str__(self):
        return json.dumps(self.data)

    def id(self):
        return self.data["id"]

    def is_status(self):
        return self.status() is not None

    def status(self):
        if "details" in self.data and len(self.data["details"]) > 0:
            for i in self.data["details"]:
                if i["name"] == "status_id":
                    return int(i["new_value"])
        return None

    def created_on(self):
        return parse_datetime(self.data["created_on"])

    def created_on_date(self):
        return trunc_datetime(self.created_on())

    def created_on_seconds(self):
        return datetime_to_seconds(self.data["created_on"])


class State:
    def __init__(self, data, journal=None, issue=None):
        self.raw = data
        self.data = data
        if journal != None:
            self.data["journal_id"] = journal.id()
            self.data["user"] = journal.data["user"]
            self.data["created_on"] = journal.data["created_on"]

        if issue != None:
            self.data["issue_id"] = issue.id()
            self.data["project_id"] = issue.project_id()

        self.plain_values = tree_to_plain(self.data)

    def get_data(self):
        return self.data

    def status(self):
        return self.data["new_value"]

    def previous_status(self):
        return self.data["old_value"]

    def create_on_date(self):
        return trunc_datetime(datetime.strptime(self.data["created_on"], '%Y-%m-%dT%H:%M:%SZ'))

    def create_on(self):
        return datetime.strptime(self.data["created_on"], '%Y-%m-%dT%H:%M:%SZ')

    def __str__(self) -> str:
        return json.dumps(self.get_data())


class Progress:
    def __init__(self, baseUrl, key):
        self.baseUrl = baseUrl
        self.key = key

    def rawQuery(self, url):
        result = requests.get(url, headers={'X-Redmine-API-Key': self.key})
        return result.json()

    def query(self, url, filters=[]):
        query = f"{self.baseUrl}{url}?utf8=✓&set_filter=1"

        for filter in filters:
            query = query + "&" + filter

        # sys.stderr.write(query)

        return self.rawQuery(query)

    def prepare_filter(self, key, values, operator):
        if isinstance(values, list):
            str = f"f[]={key}&op[{key}]={operator}"
            for value in values:
                str = str + f"&v[{key}][]={value}"
            return str
        else:
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

    def issues(self, project, filters=[]):
        return Issues(self.query(f"/projects/{project}/issues.json", filters))

    def issue(self, id, includes):
        return Issue(self.query(f"/issues/{id}.json", includes))


class ProgressSQLiteCacheAdapter:
    def __init__(self):
        self.fields = {
            "issue": {
                "type.id": {"source_field": "tracker.id"},
                "type.name": {"source_field": "tracker.name"},
                "start_date": {"source_type": "DATE"},
                "due_date": {"source_type": "DATE"},
                "created_on": {"source_type": "DATETIME"},
                "updated_on": {"source_type": "DATETIME"},
                "closed_on": {"source_type": "DATETIME"},
            },
            "state": {
                "created_on": {"source_type": "DATETIME"}
            }
        }

    def to_database(self, table, field, values):
        if table in self.fields:
            adaptation = self.fields[table]
        else:
            raise f"Table {table} is not defined"

        field_name = field["name"]
        if field_name in values:
            value = values[field_name]
        else:
            value = None

        if field_name in adaptation:
            field_adaptation = adaptation[field_name]

            if "source_field" in field_adaptation:
                source_field = field_adaptation["source_field"]

                if source_field in values:
                    value = values[source_field]
                else:
                    raise f"Source field {source_field} is not in values from incomming data field {field_name}"

            if "source_type" in field_adaptation:
                source_type = field_adaptation["source_type"]
                if source_type == "DATETIME":
                    if value is not None:
                        value = datetime_to_seconds(value)
                elif source_type == "DATE":
                    if value is not None:
                        value = date_to_seconds(value)
                else:
                    raise f"Invalid source_type {source_type}"

        return value

    def from_database(self, table, field, value, output_values):
        if table in self.fields:
            adaptation = self.fields[table]
        else:
            raise f"Table {table} is not defined"

        field_name = field["name"]

        if field_name in adaptation:
            field_adaptation = adaptation[field_name]

            if "source_field" in field_adaptation:
                field_name = field_adaptation["source_field"]

            if "source_type" in field_adaptation:
                source_type = field_adaptation["source_type"]
                if source_type == "DATETIME":
                    if value is not None:
                        value = datetime_from_seconds(value)
                elif source_type == "DATE":
                    if value is not None:
                        value = date_from_seconds(value)
                else:
                    raise f"Invalid source_type {source_type}"

        output_values[field_name] = value
