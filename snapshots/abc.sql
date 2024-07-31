{% snapshot abc %}
{{
  config({    
    "check_cols": ['first_name'],
    "strategy": 'check',
    "target_schema": 'dev',
    "unique_key": 'id'
  })
}}

WITH raw_customers AS (

  SELECT *
  
  FROM {{ ref('raw_customers')}}

)

SELECT *

FROM raw_customers

{% endsnapshot %}
