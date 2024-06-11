import os
import sys
import pendulum
from datetime import timedelta
import airflow
from airflow import DAG
from airflow.models.param import Param
from airflow.decorators import task
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from vaibhavgk3s_vaibhav_1_jafjaf_new_job.tasks import Model_1, Python_0
PROPHECY_RELEASE_TAG = "__PROJECT_ID_PLACEHOLDER__/__PROJECT_RELEASE_VERSION_PLACEHOLDER__"

with DAG(
    dag_id = "vaibhavgk3s_vaibhav_1_jafjaf_new_job", 
    schedule_interval = None, 
    default_args = {"owner" : "Prophecy", "ignore_first_depends_on_past" : True, "do_xcom_push" : True}, 
    start_date = pendulum.today('UTC'), 
    end_date = pendulum.datetime(2024, 6, 14, tz = "UTC"), 
    catchup = False, 
    max_active_runs = 1
) as dag:
    Python_0_op = Python_0()
    Model_1_op = Model_1()
