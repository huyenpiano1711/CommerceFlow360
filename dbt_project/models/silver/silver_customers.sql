-- silver_customers | Grain: 1 dòng / customer_id | Task C02 (Duy Lê)
-- customer_id gắn với từng đơn; customer_unique_id nhận diện một người mua qua nhiều đơn.
-- Giữ cả hai mã để Gold xây dim_customer theo customer_unique_id.
with src as (
    select
        {{ clean_id('customer_id') }}                                       as customer_id,
        {{ clean_id('customer_unique_id') }}                                as customer_unique_id,
        {{ clean_zip('customer_zip_code_prefix') }}                         as customer_zip_code_prefix,
        {{ clean_city('customer_city', 'customer_state') }}                 as customer_city,
        {{ clean_state('customer_state') }}                                 as customer_state,
        row_number() over (
            partition by {{ clean_id('customer_id') }}
            order by {{ bronze_latest_first(source('bronze', 'customers')) }}
        ) as _rn
    from {{ source('bronze', 'customers') }}
    where {{ clean_id('customer_id') }} is not null
)

select customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
from src
where _rn = 1
