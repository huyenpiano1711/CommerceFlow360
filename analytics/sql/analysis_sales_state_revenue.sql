-- E04 (Quỳnh Kha) | 4.2 Phân tích doanh thu | Top 10 bang khách hàng theo doanh thu
select
    coalesce(customer_state, 'unknown')            as customer_state,
    sum(revenue)                                   as revenue,
    count(distinct order_id)                       as order_count,
    round(sum(revenue) / count(distinct order_id), 2) as avg_order_value
from mart_sales
where is_valid_sale
group by customer_state
order by revenue desc
limit 10;
