-- E04 (Quỳnh Kha) | 4.3 Phân tích vận hành giao hàng | Tỷ lệ giao trễ theo người bán
-- (chỉ xét người bán có >= 30 đơn giao để tránh nhiễu từ mẫu quá nhỏ)
-- Mẫu số thống nhất với analysis_delivery_late_rate_by_state.sql: chỉ đơn delivered có đủ mốc thời gian.
-- Quy ước: mart_delivery có 1 dòng / (đơn, người bán) nên đơn nhiều người bán được tính cho mỗi người bán,
-- và điểm review của đơn được gán chung cho mọi người bán của đơn đó (Olist chỉ đánh giá theo đơn).
select
    seller_id,
    count(distinct order_id)                   as order_count,
    round(avg(is_delivered_late::int), 4)       as late_rate,
    round(avg(review_score), 2)                 as avg_review_score
from mart_delivery
where order_status = 'delivered'
  and is_delivered_late is not null
group by seller_id
having count(distinct order_id) >= 30
order by late_rate desc, seller_id
limit 10;
