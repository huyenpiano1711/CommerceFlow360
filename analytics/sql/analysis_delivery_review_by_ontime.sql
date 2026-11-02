-- E04 (Quỳnh Kha) | 4.3 Phân tích vận hành giao hàng | Điểm đánh giá trung bình: đúng hạn vs trễ
with orders_dedup as (
    select distinct order_id, is_delivered_late, review_score
    from mart_delivery
    where order_status = 'delivered'
)
select
    case when is_delivered_late then 'giao trễ' else 'đúng hạn' end as nhom_giao_hang,
    count(*)                                   as order_count,
    round(avg(review_score), 2)                as avg_review_score
from orders_dedup
where is_delivered_late is not null and review_score is not null
group by is_delivered_late
order by is_delivered_late;
