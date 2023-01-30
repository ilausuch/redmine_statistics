from enum import Enum

TRACKER_ACTION = 4
TRACKER_COORDINATION = 6


class Status(Enum):
    NEW = 1
    WORKABLE = 12
    IN_PROGRESS = 2
    BLOCKED = 15
    RESOLVED = 3
    FEEDBACK = 4
    CLOSED = 5
    REJECTED = 6


class Priority(Enum):
    IMMEDIATE = 7
    URGENT = 6
    HIGH = 5
    NORMAL = 4
    LOW = 3
