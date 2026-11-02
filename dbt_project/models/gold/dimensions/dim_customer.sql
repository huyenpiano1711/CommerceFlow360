{{ config(materialized='table') }}

with customers as (

    select distinct
        cast(customer_unique_id as varchar) as customer_unique_id
    from {{ ref('silver_customers') }}
    where customer_unique_id is not null

)

select
    row_number() over (
        order by customer_unique_id
    )::bigint as customer_key,
    customer_unique_id
from customers