from prophecy_job_databricks_cloned_job.utils import *

def Script_0():
    from airflow.operators.python import PythonOperator

    return PythonOperator(
        task_id = "Script_0",
        python_callable = lambda *args, **kwargs: exec("def m():\n    return \"abc\""),
    )
