{{ config(materialized='table') }}

-- dim_geography | Grain: 1 dòng / ZIP prefix (5 ký tự) | Task D02
-- Tọa độ, thành phố, bang ưu tiên lấy từ silver_geolocation (đã gộp 1 dòng / ZIP).
-- [Sửa logic] 162 ZIP của khách hàng/người bán không có trong bảng geolocation, trước đây
-- city/state = NULL nên ~300 dòng hàng bị rơi khỏi mọi phân tích theo bang.
-- Nay bổ sung city/state từ chính địa chỉ khách hàng/người bán (giá trị phổ biến nhất trong ZIP);
-- tọa độ vẫn để NULL vì nguồn không có, không tự gán. Cột location_source cho biết nguồn.

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

),

-- Địa chỉ khai báo của khách hàng và người bán, dùng làm nguồn dự phòng cho city/state
address_points as (

    select customer_zip_code_prefix as zip_code_prefix,
           customer_city as city,
           customer_state as state
    from {{ ref('silver_customers') }}

    union all

    select seller_zip_code_prefix, seller_city, seller_state
    from {{ ref('silver_sellers') }}

),

address_state as (

    select zip_code_prefix, state,
           row_number() over (partition by zip_code_prefix order by count(*) desc, state) as rk
    from address_points
    where zip_code_prefix is not null and state is not null
    group by zip_code_prefix, state

),

address_city as (

    select zip_code_prefix, city,
           row_number() over (partition by zip_code_prefix order by count(*) desc, city) as rk
    from address_points
    where zip_code_prefix is not null and city is not null
    group by zip_code_prefix, city

)

select
    row_number() over (
        order by zip_prefixes.zip_code_prefix
    )::bigint as geography_key,
    zip_prefixes.zip_code_prefix,
    coalesce(geolocation.city, address_city.city)    as city,
    coalesce(geolocation.state, address_state.state) as state,
    geolocation.latitude,
    geolocation.longitude,
    case
        when geolocation.state is not null then 'geolocation'
        when address_state.state is not null then 'customer_seller_address'
        else 'unknown'
    end as location_source
from zip_prefixes
left join geolocation
    on zip_prefixes.zip_code_prefix = geolocation.zip_code_prefix
left join address_state
    on zip_prefixes.zip_code_prefix = address_state.zip_code_prefix and address_state.rk = 1
left join address_city
    on zip_prefixes.zip_code_prefix = address_city.zip_code_prefix and address_city.rk = 1
