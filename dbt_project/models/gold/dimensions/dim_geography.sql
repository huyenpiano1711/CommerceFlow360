{{ config(materialized='table') }}

with zip_prefixes as (

    select customer_zip_code_prefix as zip_code_prefix
    from {{ ref('silver_customers') }}
    where customer_zip_code_prefix is not null

    union

    select seller_zip_code_prefix as zip_code_prefix
    from {{ ref('silver_sellers') }}
    where seller_zip_code_prefix is not null

    union

    select geolocation_zip_code_prefix as zip_code_prefix
    from {{ ref('silver_geolocation') }}
    where geolocation_zip_code_prefix is not null

),

geolocation as (

    select
        geolocation_zip_code_prefix as zip_code_prefix,
        geolocation_city as city,
        geolocation_state as state,
        geolocation_lat as latitude,
        geolocation_lng as longitude
    from {{ ref('silver_geolocation') }}

)

select
    row_number() over (
        order by zip_prefixes.zip_code_prefix
    )::bigint as geography_key,
    zip_prefixes.zip_code_prefix,
    geolocation.city,
    geolocation.state,
    geolocation.latitude,
    geolocation.longitude
from zip_prefixes
left join geolocation
    on zip_prefixes.zip_code_prefix = geolocation.zip_code_prefix