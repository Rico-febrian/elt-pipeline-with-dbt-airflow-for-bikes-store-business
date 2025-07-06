from airflow.decorators import dag
from airflow.operators.python import BranchPythonOperator
from airflow.models import Variable
from datetime import datetime
from helper.callbacks.slack_notifier import slack_notifier

from cosmos.config import ProjectConfig, ProfileConfig, RenderConfig
from cosmos.profiles.postgres import PostgresUserPasswordProfileMapping
from cosmos.constants import TestBehavior
from cosmos import DbtTaskGroup

import os

default_args = {
    'on_failure_callback': slack_notifier
}

DBT_PROJECT_PATH = f"{os.environ['AIRFLOW_HOME']}/dags/bikes_store_warehouse/bikes_store_warehouse_dbt"

project_config = ProjectConfig(
    dbt_project_path=DBT_PROJECT_PATH,
    project_name="bikes_store_warehouse",
)

profile_config = ProfileConfig(
    profile_name="bikes_store_warehouse",
    target_name="warehouse",
    profile_mapping=PostgresUserPasswordProfileMapping(
        conn_id='warehouse',
        profile_args={"schema": "warehouse"}
    )
)

render_config_init = RenderConfig(
    dbt_executable_path="/opt/airflow/dbt_venv/bin",
    emit_datasets=True,
    test_behavior=TestBehavior.AFTER_ALL
)

render_config_warehouse = RenderConfig(
    dbt_executable_path="/opt/airflow/dbt_venv/bin",
    emit_datasets=True,
    test_behavior=TestBehavior.AFTER_ALL,
    exclude=["path:seeds/dim_date.csv"]
)


@dag(
    dag_id='bikes_store_warehouse',
    description='Transform data into warehouse',
    start_date=datetime(2024, 9, 1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args,
    tags=['dbt', 'warehouse']
)
def bikes_store_warehouse():

    def check_is_warehouse_init():
        is_init = Variable.get("BIKES_STORE_WAREHOUSE_INIT", default_var="false").lower() == "true"
        return "init_warehouse" if is_init else "warehouse"

    init_check = BranchPythonOperator(
        task_id='check_is_warehouse_init',
        python_callable=check_is_warehouse_init
    )

    init_warehouse = DbtTaskGroup(
        group_id="init_warehouse",
        project_config=project_config,
        profile_config=profile_config,
        render_config=render_config_init,
        operator_args={
            "install_deps" : True
        }
    )

    warehouse = DbtTaskGroup(
        group_id="warehouse",
        project_config=project_config,
        profile_config=profile_config,
        render_config=render_config_warehouse,
        operator_args={
            "install_deps" : True
        }            
    )

    init_check >> init_warehouse
    init_check >> warehouse

bikes_store_warehouse()
