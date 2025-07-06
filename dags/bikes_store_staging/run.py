from airflow.decorators import dag
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from helper.callbacks.slack_notifier import slack_notifier
from bikes_store_staging.tasks.main import extract, load
from pendulum import datetime
import ast

default_args = {
    'on_failure_callback': slack_notifier
}

@dag(
    dag_id='bikes_store_staging',
    description='Extract & Load bikes store data into staging',
    start_date=datetime(2024, 9, 1),
    schedule='@daily',
    catchup=False,
    default_args=default_args
)
def bikes_store_staging():
    incremental_mode = ast.literal_eval(Variable.get('BIKES_STORE_STAGING_INCREMENTAL_MODE'))

    extract_group = extract(incremental=incremental_mode)
    first_load_task, last_load_task, load_api_task = load(incremental=incremental_mode)

    trigger_dbt = TriggerDagRunOperator(
        task_id='trigger_bikes_store_warehouse',
        trigger_dag_id='bikes_store_warehouse',
    )

    extract_group >> first_load_task
    last_load_task >> trigger_dbt
    load_api_task >> trigger_dbt

bikes_store_staging()
