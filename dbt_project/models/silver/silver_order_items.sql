-- silver_order_items | Grain: 1 dòng / (order_id, order_item_id) | Task C02 (Duy Lê)
-- Quy tắc: ép kiểu số tiền sang DECIMAL(12,2), mốc giới hạn giao cho đơn vị vận chuyển sang TIMESTAMP,
-- khử trùng theo grain. Không tổng hợp ở đây để Gold tự quyết định cấp tổng hợp.
with src as (
    select
        {{ clean_id('order_id') }}                   as order_id,
        {{ clean_int('order_item_id') }}             as order_item_id,
        {{ clean_id('product_id') }}                 as product_id,
        {{ clean_id('seller_id') }}                  as seller_id,
        {{ clean_timestamp('shipping_limit_date') }} as shipping_limit_date,
        {{ clean_money('price') }}                   as price,
        {{ clean_money('freight_value') }}           as freight_value,
        row_number() over (
            partition by {{ clean_id('order_id') }}, {{ clean_int('order_item_id') }}
            order by {{ bronze_latest_first(source('bronze', 'order_items')) }}
        ) as _rn
    from {{ source('bronze', 'order_items') }}
    where {{ clean_id('order_id') }} is not null
)

select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value,
    price + freight_value                          as item_total_value
from src
where _rn = 1
