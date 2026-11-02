-- silver_orders | Grain: 1 dòng / order_id | Task C02 (Duy Lê)
-- Quy tắc: ép kiểu các mốc thời gian, chuẩn hóa order_status, khử trùng theo order_id,
-- KHÔNG xóa đơn thiếu ngày giao (đơn chưa giao là hợp lệ nghiệp vụ) mà gắn cờ chất lượng.
with src as (
    select
        {{ clean_id('order_id') }}                                 as order_id,
        {{ clean_id('customer_id') }}                              as customer_id,
        {{ clean_code('order_status') }}                           as order_status,
        {{ clean_timestamp('order_purchase_timestamp') }}          as order_purchase_timestamp,
        {{ clean_timestamp('order_approved_at') }}                 as order_approved_at,
        {{ clean_timestamp('order_delivered_carrier_date') }}      as order_delivered_carrier_date,
        {{ clean_timestamp('order_delivered_customer_date') }}     as order_delivered_customer_date,
        {{ clean_timestamp('order_estimated_delivery_date') }}     as order_estimated_delivery_date,
        row_number() over (
            partition by {{ clean_id('order_id') }}
            order by {{ bronze_latest_first(source('bronze', 'orders')) }}
        ) as _rn
    from {{ source('bronze', 'orders') }}
    where {{ clean_id('order_id') }} is not null
)

select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    cast(order_purchase_timestamp as date)                      as order_purchase_date,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    -- Cờ chất lượng: giữ nguyên giá trị gốc, chỉ đánh dấu để Gold/Data Mart quyết định loại trừ
    (order_status = 'delivered' and order_delivered_customer_date is null)
                                                                as flag_delivered_missing_date,
    coalesce(order_delivered_carrier_date < order_purchase_timestamp, false)
                                                                as flag_carrier_before_purchase,
    coalesce(order_delivered_customer_date < order_delivered_carrier_date, false)
                                                                as flag_customer_before_carrier
from src
where _rn = 1
