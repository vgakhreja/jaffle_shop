from vaibhavgk3s_vaibhav_1_jafjaf_airflow_clone.utils import *
from vaibhavgk3s_vaibhav_1_jafjaf_airflow_clone.utils.tableau_extract import *

def TableauExtract_1():
    from airflow.operators.python import PythonOperator
    from datetime import timedelta

    return PythonOperator(
        task_id = "TableauExtract_1",
        python_callable = export_tableau_hyperfile,
        op_kwargs = {
          "source_type": "SNOWFLAKE",
          "hyper_path": "customers.hyper",
          "hyper_name": 'Extract',
          "tableau_conn_id": "tableau_ashish",
          "project_name": "Samples",
          "warehouse_conn_id": "snowflake_CICD_253",
          "table_name": "customers",
          "database_name": None,
          "catalog_name": None,
          "profile_dir": None,
          "dbt_profile": None
        },
    )
