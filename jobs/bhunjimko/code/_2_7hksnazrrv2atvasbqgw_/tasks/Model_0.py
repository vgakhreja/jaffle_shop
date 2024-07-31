from _2_7hksnazrrv2atvasbqgw_.utils import *

def Model_0():
    from airflow.operators.python import PythonOperator
    from datetime import timedelta
    import os
    import zipfile
    import tempfile

    return PythonOperator(
        task_id = "Model_0",
        python_callable = invoke_dbt_runner,
        op_kwargs = {
          "is_adhoc_run_from_same_project": False,
          "is_prophecy_managed": True,
          "run_deps": False,
          "run_seeds": True,
          "run_parents": False,
          "run_children": False,
          "run_tests": True,
          "run_mode": "model",
          "entity_kind": None,
          "entity_name": "stg_payments",
          "project_id": "62",
          "git_entity": "branch",
          "git_entity_value": "dev",
          "git_ssh_url": "https://github.com/vgakhreja/jaffle_shop",
          "git_sub_path": "",
          "select": "",
          "exclude": "",
          "run_props": " --profile run_profile",
          "envs": {"DBT_DATABRICKS_INVOCATION_ENV" : "prophecy"}, 
          "git_token_secret": "0g3Xq1RJ8z_CvBovjskz8g_", 
          "dbt_profile_secret": "vhsnuaZIeCeHjS3uHtY0i"
        },
    )
