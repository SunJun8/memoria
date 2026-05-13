from __future__ import annotations

from memoria.application.services.sleep_service import SleepService
from memoria.domain.enums import JobType


class AssociationService(SleepService):
    """Runs active association jobs with the same worker flow as sleep."""

    _job_type = JobType.ASSOCIATE.value
