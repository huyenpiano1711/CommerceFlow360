-- E04 (Quỳnh Kha) | 4.3 Phân tích vận hành giao hàng | Tỷ lệ giao trễ theo người bán
-- (chỉ xét người bán có >= 30 đơn giao để tránh nhiễu từ mẫu quá nhỏ)
select
    seller_id,
    count(distinct order_id)                   as order_count,
    round(avg(is_delivered_late::int), 4)       as late_rate,
    round(avg(review_score), 2)                 as avg_review_score
from mart_delivery
where order_status = 'delivered'
group by seller_id
having count(distinct order_id) >= 30
order by late_rate desc
limit 10;
