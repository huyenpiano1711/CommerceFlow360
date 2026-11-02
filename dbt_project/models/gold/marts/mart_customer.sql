{{ config(materialized='table') }}

-- mart_customer | Grain: 1 dòng / customer_unique_id | Task E03 (Quỳnh Kha)
-- Số đơn, tổng chi tiêu (payment_value - giá trị khách thực trả), thời gian từ lần mua gần
-- nhất, cờ khách mua lại. "Thời gian từ lần mua gần nhất" không có mốc "hôm nay" hợp lý với
-- dữ liệu lịch sử Olist (2016-2018) nên dùng ngày đặt hàng lớn nhất toàn dữ liệu làm mốc so sánh
-- (snapshot_date), tương đương kỹ thuật phân tích RFM trên dữ liệu lịch sử.
with orders_with_date as (
    select
        orders.customer_key,
        orders.order_id,
        order_date.full_date as order_purchase_date
    from {{ ref('fact_orders') }} as orders
    left join {{ ref('dim_date') }} as order_date
        on orders.purchase_date_key = order_date.date_key
    where orders.customer_key is not null
),

customer_orders as (
    select
        customer_key,
        count(distinct order_id)      as order_count,
        min(order_purchase_date)      as first_order_date,
        max(order_purchase_date)      as last_order_date
    from orders_with_date
    group by customer_key
),

customer_spend as (
    select
        customer_key,
        sum(payment_value) as total_spend
    from {{ ref('fact_payments') }}
    where customer_key is not null
    group by customer_key
),

snapshot as (
    select max(order_purchase_date) as snapshot_date
    from orders_with_date
)

select
    customer.customer_key,
    customer.customer_unique_id,
    coalesce(orders.order_count, 0)              as order_count,
    coalesce(spend.total_spend, 0)                as total_spend,
    orders.first_order_date,
    orders.last_order_date,
    date_diff('day', orders.last_order_date, snapshot.snapshot_date)
                                                   as days_since_last_order,
    coalesce(orders.order_count, 0) > 1           as is_repeat_customer

from {{ ref('dim_customer') }} as customer
left join customer_orders as orders
    on orders.customer_key = customer.customer_key
left join customer_spend as spend
    on spend.customer_key = customer.customer_key
cross join snapshot
