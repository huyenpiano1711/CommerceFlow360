-- test_silver_delivery_dates | Task C03 (Duy Lê)
-- Quy tắc nghiệp vụ: ngày khách nhận hàng không được trước thời điểm đặt hàng,
-- và ngày giao dự kiến không được trước thời điểm đặt hàng.
-- Test PASS khi truy vấn trả về 0 dòng.
select
    order_id,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date
from {{ ref('silver_orders') }}
where order_delivered_customer_date < order_purchase_timestamp
   or cast(order_estimated_delivery_date as date) < cast(order_purchase_timestamp as date)
