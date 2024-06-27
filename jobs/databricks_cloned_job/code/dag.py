import os
import sys
import pendulum
from datetime import timedelta
import airflow
from airflow import DAG
from airflow.models.param import Param
from airflow.decorators import task
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from prophecy_job_databricks_cloned_job.tasks import Script_0
PROPHECY_RELEASE_TAG = "__PROJECT_ID_PLACEHOLDER__/__PROJECT_RELEASE_VERSION_PLACEHOLDER__"

with DAG(
    dag_id = "Prophecy_Job_databricks_cloned_job", 
    schedule_interval = None, 
    default_args = {"owner" : "Prophecy", "retries" : 0}, 
    start_date = pendulum.today('UTC')
) as dag:
    Script_0_op = Script_0()
