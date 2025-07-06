from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowSkipException
from airflow import AirflowException
from airflow.models import Variable

from helper.minio import CustomMinio
from datetime import timedelta

import pandas as pd
import requests

class Extract:
    @staticmethod
    def _bikes_store(schema, table_name, incremental, **kwargs):
        try:
            pg_hook = PostgresHook(postgres_conn_id='bikes-store-db')
            connection = pg_hook.get_conn()
            cursor = connection.cursor()

            query = f"SELECT * FROM {schema}.{table_name}"
            if incremental:
                date = kwargs['ds']
                query += f" WHERE last_update::DATE = '{date}'::DATE - INTERVAL '1 DAY';"

                object_name = f'/sources/{schema}.{table_name}-{(pd.to_datetime(date) - timedelta(days=1)).strftime("%Y-%m-%d")}.csv'
            
            else:
                object_name = f'/sources/{schema}.{table_name}.csv'

            cursor.execute(query)
            result = cursor.fetchall()
            column_list = [desc[0] for desc in cursor.description]
            
            cursor.close()
            connection.commit()
            connection.close()

            df = pd.DataFrame(result, columns=column_list)
        
            if df.empty:
                raise AirflowSkipException(f"{schema}.{table_name} doesn't have new data. Skipped...")

            bucket_name = 'bikes-store'
            CustomMinio._put_csv(df, bucket_name, object_name)

        except AirflowSkipException as e:
            raise e
        except Exception as e:
            raise AirflowException(f"Error when extracting {table_name} : {str(e)}")
        
        
    @staticmethod
    def _bikes_store_api():
        """
        Extract data from bikes store API.

        Args:
            ds (str): Date string.

        Raises:
            AirflowException: If failed to fetch data from bikes store API.
            AirflowSkipException: If no new data is found.
        """
        try:
            response = requests.get(url=Variable.get('BIKES_STORE_API_URL'))

            if response.status_code != 200:
                raise AirflowException(f"Failed to fetch data from Dellstore API. Status code: {response.status_code}")

            json_data = response.json()
            
            df = pd.DataFrame(json_data)
            
            bucket_name = 'bikes-store'
            object_name = f'sources/currency.csv'
            
            if not df.empty:
                CustomMinio._put_csv(df, bucket_name, object_name)
            else:
                raise ValueError("Empty dataframe returned from API.")
   
        except AirflowException as e:
            raise e
        
        except Exception as e:
            raise AirflowException(f"Error when extracting bike store API: {str(e)}")