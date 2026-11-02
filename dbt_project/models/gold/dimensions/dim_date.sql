{{ config(materialized='table') }}

with calendar as (

    select
        cast(date_value as date) as full_date
    from generate_series(
        date '2016-01-01',
        date '2018-12-31',
        interval 1 day
    ) as dates(date_value)

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