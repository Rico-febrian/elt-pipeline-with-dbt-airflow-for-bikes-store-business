from airflow.decorators import task_group
from airflow.operators.python import PythonOperator
from bikes_store_staging.tasks.components.load import Load


@task_group()
def load_api():
    task = PythonOperator(
        task_id='currency_data',
        python_callable=Load._bikes_store_api,
        trigger_rule='none_failed'
    )
    
    return task
