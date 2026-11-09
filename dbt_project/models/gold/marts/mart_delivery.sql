{{ config(materialized='table') }}

-- mart_delivery | Grain: 1 dòng / (order_id, seller_id tham gia đơn) | Task E02 (Quỳnh Kha)
-- Một đơn có thể có nhiều người bán (nhiều dòng hàng khác seller) nên tách theo cặp
-- (order_id, seller) để tính tỷ lệ giao trễ "theo người bán"; delivery_days/days_late là
-- chỉ số ở cấp đơn nên lặp lại trên các dòng seller của cùng một đơn - khi gộp toàn mart cần
-- dùng count(distinct order_id) chứ không phải count(*), và review_score chỉ tính 1 lần/đơn
-- (đã lọc is_latest_review ở fact_reviews) nên cũng bị lặp theo seller vì lý do tương tự.
--
-- QUY ƯỚC review theo người bán: Olist chỉ cho khách đánh giá cả đơn, không đánh giá từng người bán.
-- Đơn nhiều người bán thì mọi người bán của đơn nhận CHUNG điểm review đó (không chia, không suy ra
-- điểm riêng). Điểm TB theo người bán vì vậy là "điểm của các đơn người bán tham gia".
-- Khi tính điểm TB toàn bộ / theo bang phải khử trùng theo order_id trước.
with order_sellers as (
    select distinct
        order_id,
        seller_key,
        seller_geography_key
    from {{ ref('fact_order_items') }}
),

latest_review as (
    select order_id, review_score
    from {{ ref('fact_reviews') }}
    where is_latest_review
)

select
    orders.order_id,
    seller.seller_id,
    seller_geo.state                            as seller_state,
    customer_geo.state                           as customer_state,
    order_date.year,
    order_date.month,
    order_date.month_name,
    orders.order_status,
    orders.delivery_days,
    orders.days_late,
    orders.is_delivered_late,
    review.review_score

from {{ ref('fact_orders') }} as orders
join order_sellers
    on order_sellers.order_id = orders.order_id
left join {{ ref('dim_seller') }} as seller
    on order_sellers.seller_key = seller.seller_key
left join {{ ref('dim_geography') }} as seller_geo
    on order_sellers.seller_geography_key = seller_geo.geography_key
left join {{ ref('dim_geography') }} as customer_geo
    on orders.customer_geography_key = customer_geo.geography_key
left join {{ ref('dim_date') }} as order_date
    on orders.purchase_date_key = order_date.date_key
left join latest_review as review
    on review.order_id = orders.order_id
