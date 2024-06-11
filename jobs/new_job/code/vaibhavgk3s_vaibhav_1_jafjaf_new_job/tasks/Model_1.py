from vaibhavgk3s_vaibhav_1_jafjaf_new_job.utils import *

def Model_1():
    from airflow.operators.bash import BashOperator
    import os
    import zipfile
    import tempfile
    envs = {"DBT_DATABRICKS_INVOCATION_ENV" : "prophecy"}
    dbt_props_cmd = ""

    if "":
        envs = {"DBT_DATABRICKS_INVOCATION_ENV" : "prophecy", "DBT_PROFILES_DIR" : ""}

    if "":
        dbt_props_cmd = " --profile "

    return BashOperator(
        task_id = "Model_1",
        bash_command = " && ".join(
          ["{} && cd $tmpDir/{}".format(
             (
               "set -euxo pipefail && tmpDir=`mktemp -d` && git clone "
               + "{} $tmpDir && git checkout {}".format("https://github.com/vgakhreja/jaffle_shop", None)
             ),
             ""
           ),            "dbt seed" + dbt_props_cmd,  "dbt run" + dbt_props_cmd,  "dbt test" + dbt_props_cmd]
        ),
        env = envs,
        append_env = True,
    )
