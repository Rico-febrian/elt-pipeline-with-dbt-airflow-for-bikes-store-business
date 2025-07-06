from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowSkipException
from airflow import AirflowException

from helper.minio import CustomMinio, MinioClient
from sqlalchemy import create_engine
from pangres import upsert
from datetime import timedelta
from minio.error import S3Error 

import pandas as pd
import io

class Load:
    @staticmethod
    def _bikes_store(schema, table_name, pkey, incremental, **kwargs):
        date = kwargs.get('ds')

        object_name = f'/sources/{schema}.{table_name}-{(pd.to_datetime(date) - timedelta(days=1)).strftime("%Y-%m-%d")}.csv' if incremental else f'/sources/{schema}.{table_name}.csv'
        bucket_name = 'bikes-store'
        engine = create_engine(PostgresHook(postgres_conn_id='warehouse').get_uri())

        try:
            df = CustomMinio._get_dataframe(bucket_name, object_name)
            
            if df.empty:
                raise AirflowSkipException(f"Dataframe for {table_name} is empty. Skipped...")    
            
            # Set primary key
            df = df.set_index(pkey)

            upsert(
                con=engine,
                df=df,
                table_name=table_name,
                schema='bikes_store_staging',
                if_row_exists='update'
            )

            engine.dispose()
        
        except(S3Error, FileNotFoundError) as e:
            engine.dispose()
            raise AirflowSkipException(f"{table_name} doesn't have new data. Skipped... : {str(e)}")
    
        except Exception as e:
            engine.dispose()
            raise AirflowException(f"Error when loading {table_name} : {str(e)}")
        
        
    @staticmethod
    def _bikes_store_api():
        """
        Load data from bikes store API into staging area.

        """
        bucket_name = 'bikes-store'
        object_name = f'sources/currency.csv'

        try:
            engine = create_engine(PostgresHook(postgres_conn_id='warehouse').get_uri())

            try:
                minio_client = MinioClient._get()

                data = minio_client.get_object(bucket_name=bucket_name, object_name=object_name).read().decode('utf-8')
                
                df = pd.read_csv(io.StringIO(data))
                df = df.set_index('currencycode')

                upsert(
                    con=engine,
                    df=df,
                    table_name='currency',
                    schema='bikes_store_staging',
                    if_row_exists='update'
                )
            except AirflowSkipException as e:
                engine.dispose()
                raise e
            
            except Exception as e:
                engine.dispose()
                raise AirflowException(f"Error when loading data from bikes store API: {str(e)}")
            
        except AirflowSkipException as e:
            raise e
            
        except Exception as e:
            raise e