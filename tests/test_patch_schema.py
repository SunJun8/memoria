import pytest
from pydantic import ValidationError

from memoria.schemas.patches import MemoryPatch


def test_memory_patch_accepts_create_issue_and_comment():
    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "create_issue",
                    "reason": "raw entry describes a new task",
                    "confidence": 0.9,
                    "payload": {
                        "title": "Design memory system",
                        "summary": "Build a local memory system",
                        "tags": ["memoria"],
                    },
                    "refs": {"raw_entry_ids": [1]},
                }
            ],
        }
    )

    assert patch.operations[0].operation_type == "create_issue"


def test_patch_operation_keeps_job_id():
    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "create_issue",
                    "reason": "job-scoped operation",
                    "confidence": 0.9,
                    "payload": {"title": "From job"},
                    "job_id": 42,
                }
            ],
        }
    )

    assert patch.operations[0].job_id == 42


def test_memory_patch_rejects_unknown_operation():
    with pytest.raises(ValidationError):
        MemoryPatch.model_validate(
            {
                "actor": "llm",
                "source": "system_job",
                "operations": [
                    {
                        "operation_id": "op-1",
                        "operation_type": "delete_issue",
                        "reason": "not allowed",
                        "confidence": 1.0,
                        "payload": {"issue_id": 1},
                    }
                ],
            }
        )
