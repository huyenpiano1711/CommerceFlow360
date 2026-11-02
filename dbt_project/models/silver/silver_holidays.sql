-- silver_holidays | Grain: 1 dòng / holiday_date | Task C02 (Duy Lê) - bảng hỗ trợ
-- Không thuộc 9 bảng Olist nhưng được làm sạch tại Silver để dim_date ở Gold đọc từ Silver
-- (đúng nguyên tắc Medallion: Gold không đọc trực tiếp Bronze).
with src as (
    select
        try_cast({{ clean_text('date') }} as date)     as holiday_date,
        {{ clean_text('holiday_name') }}               as holiday_name,
        {{ clean_state('country_code') }}              as country_code,
        row_number() over (
            partition by try_cast({{ clean_text('date') }} as date)
            order by {{ bronze_latest_first(source('bronze', 'holidays')) }}
        ) as _rn
    from {{ source('bronze', 'holidays') }}
)

select holiday_date, holiday_name, coalesce(country_code, 'BR') as country_code, true as is_holiday
from src
where _rn = 1 and holiday_date is not null
