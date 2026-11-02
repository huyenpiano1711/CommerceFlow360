-- test_silver_non_negative_amounts | Task C03 (Duy Lê)
-- Quy tắc nghiệp vụ: giá bán phải > 0; phí vận chuyển và giá trị thanh toán không âm.
select 'order_items' as bang, order_id, 'price <= 0 hoặc freight_value < 0' as loi
from {{ ref('silver_order_items') }}
where price <= 0 or freight_value < 0
union all
select 'order_payments', order_id, 'payment_value < 0'
from {{ ref('silver_order_payments') }}
where payment_value < 0
