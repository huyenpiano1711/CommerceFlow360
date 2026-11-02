-- test_silver_order_sales_reconciliation | Task C03 (Duy Lê)
-- Đối soát giá trị tiền Bronze -> Silver: tổng price, freight_value, payment_value
-- sau khi ép kiểu DECIMAL phải bằng tổng ở Bronze (sai số làm tròn < 0,01).
with t as (
    select 'price' as chi_so,
           (select sum(try_cast(price as double)) from {{ source('bronze', 'order_items') }}) as tong_bronze,
           (select sum(price) from {{ ref('silver_order_items') }}) as tong_silver
    union all
    select 'freight_value',
           (select sum(try_cast(freight_value as double)) from {{ source('bronze', 'order_items') }}),
           (select sum(freight_value) from {{ ref('silver_order_items') }})
    union all
    select 'payment_value',
           (select sum(try_cast(payment_value as double)) from {{ source('bronze', 'order_payments') }}),
           (select sum(payment_value) from {{ ref('silver_order_payments') }})
)
select * from t where abs(tong_bronze - cast(tong_silver as double)) >= 0.01
