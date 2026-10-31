-- silver_sellers | Grain: 1 dòng / seller_id | Task C02 (Duy Lê)
-- seller_city nguồn được nhập tự do: có giá trị kèm bang ("sao paulo - sp", "maua/sao paulo"),
-- có dấu ("são paulo"), viết tắt ("sbc"), thậm chí là email hoặc số -> chuẩn hóa bằng macro clean_city.
with src as (
    select
        {{ clean_id('seller_id') }}                                  as seller_id,
        {{ clean_zip('seller_zip_code_prefix') }}                    as seller_zip_code_prefix,
        {{ clean_text('seller_city') }}                              as seller_city_raw,
        {{ clean_city('seller_city', 'seller_state') }}              as seller_city,
        {{ clean_state('seller_state') }}                            as seller_state,
        row_number() over (
            partition by {{ clean_id('seller_id') }}
            order by {{ bronze_latest_first(source('bronze', 'sellers')) }}
        ) as _rn
    from {{ source('bronze', 'sellers') }}
    where {{ clean_id('seller_id') }} is not null
)

select
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,
    (seller_city is null)                                   as flag_city_invalid,
    (seller_city is distinct from lower(seller_city_raw))   as flag_city_standardized
from src
where _rn = 1
