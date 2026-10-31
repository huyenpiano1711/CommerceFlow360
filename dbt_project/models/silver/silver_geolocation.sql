-- silver_geolocation | Grain: 1 dòng / geolocation_zip_code_prefix | Task C02 (Duy Lê)
-- Bronze có ~1 triệu dòng, nhiều dòng trùng hoàn toàn và nhiều tọa độ cho cùng một tiền tố ZIP.
-- Gộp về 1 dòng / ZIP để phép nối với khách hàng, người bán không nhân bản dữ liệu:
--   * tọa độ đại diện = trung vị (median) của các điểm nằm trong khung lãnh thổ Brazil
--     (trung vị ít bị kéo lệch bởi điểm ngoại lai hơn trung bình);
--   * bang, thành phố = giá trị xuất hiện nhiều nhất trong ZIP (hòa thì lấy theo thứ tự chữ cái);
--   * giữ các cột thống kê để truy vết quá trình gộp.
with src as (
    select
        {{ clean_zip('geolocation_zip_code_prefix') }}                       as zip_code_prefix,
        try_cast(geolocation_lat as double)                                  as lat,
        try_cast(geolocation_lng as double)                                  as lng,
        {{ clean_city('geolocation_city', 'geolocation_state') }}            as city,
        {{ clean_state('geolocation_state') }}                               as state
    from {{ source('bronze', 'geolocation') }}
),

flagged as (
    select
        *,
        (lat between {{ var('brazil_lat_min') }} and {{ var('brazil_lat_max') }}
         and lng between {{ var('brazil_lng_min') }} and {{ var('brazil_lng_max') }}) as in_brazil
    from src
    where zip_code_prefix is not null
),

coords as (
    select
        zip_code_prefix,
        median(lat) filter (where in_brazil)                as geolocation_lat,
        median(lng) filter (where in_brazil)                as geolocation_lng,
        count(*)                                            as source_row_count,
        count(distinct (lat, lng))                          as distinct_coordinate_count,
        count(*) filter (where not coalesce(in_brazil, false)) as out_of_bounds_count,
        count(distinct state)                               as distinct_state_count
    from flagged
    group by zip_code_prefix
),

state_rank as (
    select zip_code_prefix, state,
           row_number() over (partition by zip_code_prefix order by count(*) desc, state) as rk
    from flagged
    where state is not null
    group by zip_code_prefix, state
),

city_rank as (
    select zip_code_prefix, city,
           row_number() over (partition by zip_code_prefix order by count(*) desc, city) as rk
    from flagged
    where city is not null
    group by zip_code_prefix, city
)

select
    c.zip_code_prefix                         as geolocation_zip_code_prefix,
    c.geolocation_lat,
    c.geolocation_lng,
    ci.city                                   as geolocation_city,
    st.state                                  as geolocation_state,
    c.source_row_count,
    c.distinct_coordinate_count,
    c.out_of_bounds_count,
    (c.geolocation_lat is null)               as flag_no_valid_coordinate,
    (c.distinct_state_count > 1)              as flag_multiple_states
from coords c
left join state_rank st on st.zip_code_prefix = c.zip_code_prefix and st.rk = 1
left join city_rank  ci on ci.zip_code_prefix = c.zip_code_prefix and ci.rk = 1
