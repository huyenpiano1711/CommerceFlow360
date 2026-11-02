{{ config(materialized='table') }}

-- [Sửa logic] Trước đây lịch cố định 2016-01-01..2018-12-31, nhưng nguồn có shipping_limit_date
-- tới năm 2020 nên các dòng đó mất khóa ngày. Nay khoảng lịch được tính từ ngày nhỏ nhất/lớn nhất
-- của mọi cột ngày mà fact tham chiếu, làm tròn ra đầu năm/cuối năm.
with date_bounds as (

    select
        date_trunc('year', min(d))::date                                    as start_date,
        (date_trunc('year', max(d)) + interval 1 year - interval 1 day)::date as end_date
    from (
        select cast(order_purchase_timestamp as date) as d from {{ ref('silver_orders') }}
        union all select cast(order_approved_at as date) from {{ ref('silver_orders') }}
        union all select cast(order_delivered_carrier_date as date) from {{ ref('silver_orders') }}
        union all select cast(order_delivered_customer_date as date) from {{ ref('silver_orders') }}
        union all select cast(order_estimated_delivery_date as date) from {{ ref('silver_orders') }}
        union all select cast(shipping_limit_date as date) from {{ ref('silver_order_items') }}
        union all select cast(review_creation_date as date) from {{ ref('silver_order_reviews') }}
        union all select cast(review_answer_timestamp as date) from {{ ref('silver_order_reviews') }}
        union all select holiday_date from {{ ref('silver_holidays') }}
    ) all_dates

),

calendar as (

    select
        cast(unnest(generate_series(start_date, end_date, interval 1 day)) as date) as full_date
    from date_bounds

),

holidays as (

    select
        holiday_date,
        holiday_name,
        is_holiday
    from {{ ref('silver_holidays') }}

)

select
    cast(strftime(calendar.full_date, '%Y%m%d') as integer) as date_key,
    calendar.full_date,
    extract(day from calendar.full_date)::integer as day,
    extract(month from calendar.full_date)::integer as month,
    strftime(calendar.full_date, '%B') as month_name,
    extract(quarter from calendar.full_date)::integer as quarter,
    extract(year from calendar.full_date)::integer as year,
    extract(isodow from calendar.full_date)::integer as day_of_week,
    strftime(calendar.full_date, '%A') as day_name,
    extract(isodow from calendar.full_date) in (6, 7) as is_weekend,
    coalesce(holidays.is_holiday, false) as is_brazil_holiday,
    holidays.holiday_name
from calendar
left join holidays
    on calendar.full_date = holidays.holiday_date