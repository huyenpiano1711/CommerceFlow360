-- test_silver_carrier_after_purchase | Task C03 (Duy Lê) | severity = warn
-- Ngày giao cho đơn vị vận chuyển không nên sớm hơn thời điểm đặt hàng.
-- Nguồn Olist có bản ghi vi phạm; Silver giữ nguyên và gắn cờ flag_carrier_before_purchase,
-- test ở mức cảnh báo để ghi nhận số lượng trong báo cáo kiểm thử.
{{ config(severity='warn') }}
select order_id, order_purchase_timestamp, order_delivered_carrier_date
from {{ ref('silver_orders') }}
where order_delivered_carrier_date < order_purchase_timestamp
