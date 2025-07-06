from airflow.decorators import task_group
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.datasets import Dataset
from bikes_store_staging.tasks.components.load import Load


@task_group()
def load_db(incremental):
    table_to_load = Variable.get('BIKES_STORE_STAGING__table_to_extract_and_load', deserialize_json=True)
    
    previous_task = None
    first_task = None
    
    for table_name, (schema, pkey) in table_to_load.items():
        current_task = PythonOperator(
            task_id = f'{schema}.{table_name}',
            python_callable = Load._bikes_store,
            trigger_rule = 'none_failed',
            outlets = [Dataset(f'postgres://bikes-store-db-dwh:5432/warehouse.bikes-store-staging.{table_name}')],
            op_kwargs = {
                'schema' : schema,
                'table_name': table_name,
                'pkey': pkey,
                'incremental': incremental
            },
        )
        
        if previous_task:
            previous_task >> current_task
        else:
            first_task = current_task
        previous_task = current_task
        
    return first_task, previous_task
