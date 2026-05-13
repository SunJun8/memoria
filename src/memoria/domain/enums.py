from __future__ import annotations

from enum import Enum


class ProcessingState(str, Enum):
    PENDING = "pending_processing"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class IssueStatus(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    BLOCKED = "blocked"
    DONE = "done"
    ARCHIVED = "archived"


class EventType(str, Enum):
    WORK = "work_event"
    DECISION = "decision_event"
    PROBLEM = "problem_event"
    RESULT = "result_event"
    INSIGHT = "insight_event"


class LinkType(str, Enum):
    RELATES_TO = "relates_to"
    CONTINUES = "continues"
    BLOCKS = "blocks"
    DUPLICATES = "duplicates"
    CAUSED_BY = "caused_by"


class ProposalState(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class JobType(str, Enum):
    SLEEP = "sleep_consolidation"
    ASSOCIATE = "active_association"


class JobStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Strictness(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    CREATIVE = "creative"
