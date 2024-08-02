from vaibhavgk3s_vaibhav_1_jafjaf_simple_airflow_job.utils import *

def Python_1():

    def m():
        return "abc"

    import json
    from datetime import timedelta
    from airflow.operators.python import PythonOperator

    return PythonOperator(task_id = "Python_1", python_callable = m, show_return_value_in_logs = True)
