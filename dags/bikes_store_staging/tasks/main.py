from airflow.decorators import task_group
from bikes_store_staging.tasks.extract_db import extract_db
from bikes_store_staging.tasks.extract_api import extract_api
from bikes_store_staging.tasks.load_db import load_db
from bikes_store_staging.tasks.load_api import load_api


@task_group()
def extract(incremental: bool):
    db = extract_db(incremental=incremental)
    api = extract_api()
    return [db, api]


@task_group()
def load(incremental: bool):
    first_task, last_task = load_db(incremental=incremental)
    api_task = load_api()

    return first_task, last_task, api_task
