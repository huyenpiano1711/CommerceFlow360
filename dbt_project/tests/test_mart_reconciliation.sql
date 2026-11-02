-- test_mart_reconciliation | Task E01-E03 (Quỳnh Kha)
-- Đối soát Data Mart với Gold: tổng số đơn, tổng doanh thu, tổng chi tiêu khách phải khớp
-- (sai số làm tròn < 0,01) giữa mart và fact_*/dim_* nguồn, và days_since_last_order >= 0.
with reconciliations as (

    select
        'mart_sales.revenue = fact_order_items.item_price' as kiem_tra,
        cast((select sum(item_price) from {{ ref('fact_order_items') }}) as decimal(18, 2)) as nguon,
        cast((select sum(revenue) from {{ ref('mart_sales') }}) as decimal(18, 2)) as mart

    union all

    select
        -- mart_delivery chỉ gồm đơn có ít nhất 1 dòng hàng (JOIN fact_order_items để lấy seller);
        -- 775 đơn không có order_items (dữ liệu nguồn Olist) nên so với fact_order_items, không phải fact_orders.
        'mart_delivery: so don khop fact_order_items',
        cast((select count(distinct order_id) from {{ ref('fact_order_items') }}) as decimal(18, 2)),
        cast((select count(distinct order_id) from {{ ref('mart_delivery') }}) as decimal(18, 2))

    union all

    select
        'mart_customer.total_spend = fact_payments.payment_value',
        cast((select sum(payment_value) from {{ ref('fact_payments') }}) as decimal(18, 2)),
        cast((select sum(total_spend) from {{ ref('mart_customer') }}) as decimal(18, 2))

    union all

    select
        'mart_customer: tong order_count = fact_orders co customer_key',
        cast((select count(*) from {{ ref('fact_orders') }} where customer_key is not null) as decimal(18, 2)),
        cast((select sum(order_count) from {{ ref('mart_customer') }}) as decimal(18, 2))

)

select *
from reconciliations
where nguon is null or mart is null or abs(nguon - mart) >= 0.01

union all

select 'mart_customer: days_since_last_order am', null, count(*)
from {{ ref('mart_customer') }}
having count(*) filter (where days_since_last_order < 0) > 0
