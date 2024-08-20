from vaibhavgk3s_vaibhav_1_jafjaf_airflow_model.utils import *

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
          "is_prophecy_managed": False,
          "run_deps": True,
          "run_seeds": True,
          "run_parents": False,
          "run_children": False,
          "run_tests": False,
          "run_mode": "model",
          "entity_kind": "model",
          "entity_name": "stg_payments",
          "project_id": "62",
          "git_entity": "tag",
          "git_entity_value": "__PROJECT_FULL_RELEASE_TAG_PLACEHOLDER__",
          "git_ssh_url": "https://github.com/vgakhreja/jaffle_shop",
          "git_sub_path": "",
          "select": "",
          "exclude": "",
          "run_props": " --profile HelloWorld_SQL",
          "envs": {"DBT_DATABRICKS_INVOCATION_ENV" : "prophecy", "DBT_PROFILES_DIR" : "/"}
        },
    )
