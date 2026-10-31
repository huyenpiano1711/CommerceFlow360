-- silver_order_payments | Grain: 1 dòng / (order_id, payment_sequential) | Task C02 (Duy Lê)
-- Quy tắc: chuẩn hóa payment_type, ép kiểu; số kỳ trả góp = 0 là không hợp lệ
-- (mọi thanh toán có ít nhất 1 kỳ) nên đưa về 1 và gắn cờ; giữ dòng giá trị 0 (voucher, not_defined).
with src as (
    select
        {{ clean_id('order_id') }}                  as order_id,
        {{ clean_int('payment_sequential') }}       as payment_sequential,
        {{ clean_code('payment_type') }}            as payment_type,
        {{ clean_int('payment_installments') }}     as payment_installments_raw,
        {{ clean_money('payment_value') }}          as payment_value,
        row_number() over (
            partition by {{ clean_id('order_id') }}, {{ clean_int('payment_sequential') }}
            order by {{ bronze_latest_first(source('bronze', 'order_payments')) }}
        ) as _rn
    from {{ source('bronze', 'order_payments') }}
    where {{ clean_id('order_id') }} is not null
)

select
    order_id,
    payment_sequential,
    payment_type,
    case when payment_installments_raw is null or payment_installments_raw < 1 then 1
         else payment_installments_raw end           as payment_installments,
    payment_value,
    (payment_installments_raw is null or payment_installments_raw < 1)
                                                     as flag_installments_imputed,
    (payment_value = 0)                              as flag_zero_payment
from src
where _rn = 1
