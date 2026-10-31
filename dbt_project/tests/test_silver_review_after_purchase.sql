-- test_silver_review_after_purchase | Task C03 (Duy Lê) | severity = warn
-- Ngày tạo đánh giá không nên trước ngày đặt hàng. Ghi nhận ở mức cảnh báo.
{{ config(severity='warn') }}
select r.review_id, r.order_id, r.review_creation_date, o.order_purchase_timestamp
from {{ ref('silver_order_reviews') }} r
join {{ ref('silver_orders') }} o on o.order_id = r.order_id
where cast(r.review_creation_date as date) < cast(o.order_purchase_timestamp as date)
