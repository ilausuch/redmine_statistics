## About

This is a yet an other library to interact with redmine API
Author: Ivan Lausuch <ilausuch@suse.com>

## Configuration

Create the file config.py using the url and the api token

```
PROGRESS_URL = 'https://progress.opensuse.org'
PROGRESS_KEY = 'XXXX'
```

Configure the constants.py with your own parameters.
These are prepared for progress.opensuse.org

## Initialization

```
from progress import *
from config import *
from constants import *

progress = Progress( PROGRESS_URL, PROGRESS_KEY)
```

## Structure of classes

* Progress: Perform all the calls to obtain information using the Redmine API
* Issue: The wrapper for one Issue. Contains the information of an issue.
* Issues: This is a powered list of issues. Contains the different stadistical methods
* Journal: The wrapper for one element in the journal of an issue

## Issues operations

All the data is obtained with calls to an object instanced from the Progress class

### Get one issue

```
issue = progress.issue(<issue_id>, <includes>)
```
Parameters:
* issue_id: Issue id (numeric)
* includes: List of addons to include in the data (see below)

Returns:
* A Issue object

e.g. In this case we get the issue (issuedId) including the JOURNALS

```
issue = progress.issue(issueId, [
    progress.include(INCLUDE_JOURNALS)
    ])
```

#### Includes

```
INCLUDE_CHILDREN = "children"
INCLUDE_ATTACHMENTS = "attachments"
INCLUDE_RELATIONS = "relations"
INCLUDE_CHANGESETS = "changesets"
INCLUDE_JOURNALS = "journals"
INCLUTE_WATCHERS = "watchers"
INCLUDE_ALLOWED_STATUSES = "allowed_statuses"
INCLUDE_ALL = [INCLUDE_CHILDREN, INCLUDE_ATTACHMENTS, INCLUDE_RELATIONS, INCLUDE_CHANGESETS, INCLUDE_JOURNALS, INCLUTE_WATCHERS, INCLUDE_ALLOWED_STATUSES]
```

### Get multiple issues

```
issues = progress.issues(<project_name>, <filters>)
```

Parameters:
* project_name: Name of the project (str)
* filters: List of filters (see the section of filtering)

Returns a Issues object

e.g. This example shows how to get all the issues from the project that where the traker is an action and the last update is less than 10 days

```
issues = progress.issues(project, [
    progress.filter_tracker(TRACKER_ACTION),
    progress.filter_date(DATE_UPDATED, 10, DATE_COMPARATION_LESS_THAN_DAYS_AGO)
])
```

#### Filtering

Kind of filters applicable:

* status: ```filter_status(values, operator=COMPARATION_IS)```
* traker: ```filter_tracker(values, operator=COMPARATION_IS)```
* date: ```filter_date(key, date, operator)```
* two dates: ```filter_date_between(key, date1, date2)```
* tags: ```filter_tag(values, operator=COMPARATION_IS)```
* priority: ```filter_priority(values, operator=COMPARATION_IS)```

The comparation operators are:
```
COMPARATION_IS = "="
COMPARATION_IS_NOT = "!"
```

The date keys are:
```
DATE_CREATED = "created_on"
DATE_UPDATED = "updated_on"
DATE_CLOSED = "closed_on"
DATE_START = "start_date"
```

The date operatos are:
```
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
```

The priorities are:
```
PRIORITIES = [ "immediate", "urgent", "high", "normal", "low" ]
```

### Get an snapshot the status of a issue in a specific date

```
issue.getStatusByDate(<date>)
```

Parameters:
* date: datetime format

Returns:
* The status (in its numeric format)

Requisites: 
* requires to include the journals


### Get an snapshot all the status changes

Extract from the journal the status changes

```
issue.getStatusChanges()
```

Returns:
* The list of journals (Journal) that implies change of status

Requisites:
* requires to include the journals


### Get an snapshot all the status changes

### Get an snapshot the status in a specific date for a issues list

```
issues.snapshot(date)
```

Parameters:
* date: a datetime

Result:
* An Issues object that contains the list of issues with the status fixed for the requested date

Requisites:
* requires to include the journals. To load all the includes at once call to ```issues.reloadJournals()```


## Stadistical operations

All these operations require that the journals are loaded.
So before calling any of these operations call to

```
issues.reloadJournals()
```


### Get the stats counts for a day

```
issues.snapshot(<date>)
```

Parameters:
* date: the date in datetime format

Returns:
*  An dict with the counts for every status, also the ids for the issues in each status

```
issues = progress.issues(project, [
    progress.filter_tracker(TRACKER_ACTION),
    progress.filter_date(DATE_UPDATED, 10, DATE_COMPARATION_LESS_THAN_DAYS_AGO)
])

issues.reloadJournals(progress)
date = datetime.strptime(dateStr, "%Y-%m-%d")
issues = issues.snapshot(date)
print(issues.stats())
```

