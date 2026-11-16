from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from agents.agent_graph import process_command
from intelligence.memory import (
    create_job,
    update_job,
    get_job,
    list_jobs
)

executor = ThreadPoolExecutor(max_workers=2)


def run_job(job_id, command):
    try:
        update_job(job_id, "running")

        result = process_command(command)

        update_job(
            job_id,
            "completed",
            result=result
        )

    except Exception as error:
        update_job(
            job_id,
            "failed",
            error=str(error)
        )


def submit_job(command):
    job_id = str(uuid4())

    create_job(job_id, command)

    executor.submit(run_job, job_id, command)

    return get_job(job_id)


def get_job_status(job_id):
    return get_job(job_id)


def get_all_jobs(limit=20):
    return list_jobs(limit)
