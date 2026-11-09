-- E04 (Quỳnh Kha) | 4.3 Phân tích vận hành giao hàng | Tỷ lệ giao trễ theo bang khách hàng (top 10 đơn nhiều nhất)
-- mart_delivery có grain (order_id, seller_id): dedup theo order_id trước khi tính tỷ lệ
-- để không đếm lặp các đơn có nhiều người bán (xem ghi chú trong mart_delivery.sql).
-- Mẫu số thống nhất với analysis_delivery_late_rate_by_seller.sql và dashboard: chỉ đơn delivered
-- có đủ mốc thời gian (is_delivered_late khác NULL); số đơn và tỷ lệ cùng tính trên tập này.
with orders_dedup as (
    select distinct order_id, customer_state, is_delivered_late, days_late
    from mart_delivery
    where order_status = 'delivered'
      and is_delivered_late is not null
)
select
    coalesce(customer_state, 'unknown')                          as customer_state,
    count(*)                                                     as order_count,
    round(avg(is_delivered_late::int), 4)                        as late_rate,
    round(avg(days_late), 2)                                     as avg_days_late
from orders_dedup
group by customer_state
order by order_count desc
limit 10;
