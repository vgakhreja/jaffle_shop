from npqx8dog5yo5cr7bnikwaq_.utils import *

def Email_0():
    from airflow.operators.email import EmailOperator
    from datetime import timedelta

    return EmailOperator(
        task_id = "Email_0",
        to = "vaibhav@prophecy.io",
        subject = "abc",
        html_content = "abc",
        cc = None,
        bcc = None,
        mime_subtype = "mixed",
        mime_charset = "utf-8",
        conn_id = "5BxrU6J0NxpCihZx2YSOk",
    )
