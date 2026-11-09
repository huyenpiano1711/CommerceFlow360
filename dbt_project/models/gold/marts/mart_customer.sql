{{ config(materialized='table') }}

-- mart_customer | Grain: 1 dòng / customer_unique_id | Task E03 (Quỳnh Kha)
-- Số đơn, tổng chi tiêu (payment_value - giá trị khách thực trả), thời gian từ lần mua gần
-- nhất, cờ khách mua lại. "Thời gian từ lần mua gần nhất" không có mốc "hôm nay" hợp lý với
-- dữ liệu lịch sử Olist (2016-2018) nên dùng ngày đặt hàng lớn nhất toàn dữ liệu làm mốc so sánh
-- (snapshot_date), tương đương kỹ thuật phân tích RFM trên dữ liệu lịch sử.
--
-- [Sửa logic] Thống nhất KPI với mart_sales: số đơn, tổng chi tiêu, ngày mua đầu/cuối và cờ mua lại
-- chỉ tính trên ĐƠN HỢP LỆ (fact_orders.is_valid_order, loại canceled/unavailable). Trước đây mart này
-- đếm cả đơn hủy nên khách chỉ có 1 đơn thật + 1 đơn hủy bị tính là "khách mua lại".
-- Khách không có đơn hợp lệ nào vẫn giữ trong mart (has_valid_order = false) để đối soát với dim_customer,
-- nhưng phải lọc has_valid_order khi tính tỷ lệ mua lại, recency, phân khúc chi tiêu.
--
-- QUY TẮC tổng chi tiêu: total_spend = tổng payment_value có trong nguồn của các đơn hợp lệ.
-- Đơn hợp lệ không có dòng thanh toán nào (nguồn thiếu dữ liệu) vẫn được đếm trong order_count nhưng
-- góp 0 vào total_spend - không tự suy ra số tiền từ giá hàng. Số đơn này ghi ở orders_without_payment
-- để đối soát (tests/test_mart_reconciliation.sql). Khách của thanh toán lấy theo fact_orders.customer_key.
with orders_with_date as (
    select
        orders.customer_key,
        orders.order_id,
        orders.is_valid_order,
        order_date.full_date as order_purchase_date,
        exists (
            select 1 from {{ ref('fact_payments') }} as payments where payments.order_id = orders.order_id
        ) as has_payment
    from {{ ref('fact_orders') }} as orders
    left join {{ ref('dim_date') }} as order_date
        on orders.purchase_date_key = order_date.date_key
    where orders.customer_key is not null
),

customer_orders as (
    select
        customer_key,
        count(distinct order_id)                                    as order_count_all_status,
        count(distinct order_id) filter (where is_valid_order)      as order_count,
        count(distinct order_id) filter (where is_valid_order and not has_payment)
                                                                    as orders_without_payment,
        min(order_purchase_date) filter (where is_valid_order)      as first_order_date,
        max(order_purchase_date) filter (where is_valid_order)      as last_order_date
    from orders_with_date
    group by customer_key
),

customer_spend as (
    select
        orders.customer_key,
        sum(payments.payment_value) as total_spend
    from {{ ref('fact_payments') }} as payments
    join {{ ref('fact_orders') }} as orders
        on payments.order_id = orders.order_id
    where orders.customer_key is not null
      and orders.is_valid_order
    group by orders.customer_key
),

snapshot as (
    select max(order_purchase_date) as snapshot_date
    from orders_with_date
)

select
    customer.customer_key,
    customer.customer_unique_id,
    coalesce(orders.order_count, 0)               as order_count,
    coalesce(orders.order_count_all_status, 0)    as order_count_all_status,
    coalesce(orders.orders_without_payment, 0)    as orders_without_payment,
    coalesce(spend.total_spend, 0)                as total_spend,
    orders.first_order_date,
    orders.last_order_date,
    date_diff('day', orders.last_order_date, snapshot.snapshot_date)
                                                   as days_since_last_order,
    coalesce(orders.order_count, 0) > 0           as has_valid_order,
    coalesce(orders.order_count, 0) > 1           as is_repeat_customer

from {{ ref('dim_customer') }} as customer
left join customer_orders as orders
    on orders.customer_key = customer.customer_key
left join customer_spend as spend
    on spend.customer_key = customer.customer_key
cross join snapshot
