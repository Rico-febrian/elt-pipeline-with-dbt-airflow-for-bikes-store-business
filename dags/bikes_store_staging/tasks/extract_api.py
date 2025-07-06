from airflow.decorators import task_group
from airflow.operators.python import PythonOperator
from bikes_store_staging.tasks.components.extract import Extract


@task_group()
def extract_api():
    task = PythonOperator(
        task_id = 'currency_data',
        python_callable = Extract._bikes_store_api,
        trigger_rule = 'none_failed'
    )
    
    return task