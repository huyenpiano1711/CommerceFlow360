{{ config(materialized='table') }}

with sellers as (

    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    from {{ ref('silver_sellers') }}

)

select
    row_number() over (
        order by seller_id
    )::bigint as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
from sellers