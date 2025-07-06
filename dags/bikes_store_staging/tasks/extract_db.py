from airflow.decorators import task_group
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.datasets import Dataset
from bikes_store_staging.tasks.components.extract import Extract


@task_group()
def extract_db(incremental):
        
    table_to_extract = Variable.get('BIKES_STORE_STAGING__table_to_extract_and_load', deserialize_json=True)

    for table_name, (schema, _) in table_to_extract.items():
        PythonOperator(
            task_id = f'{schema}.{table_name}',
            python_callable = Extract._bikes_store,
            trigger_rule = 'none_failed',
            outlets = [Dataset(f'postgres://bikes-store-db-src:5432/bikes-store.bikes-store.{table_name}')],
            op_kwargs = {
                'schema' : f'{schema}',
                'table_name': f'{table_name}',
                'incremental': incremental
            }
        )
        