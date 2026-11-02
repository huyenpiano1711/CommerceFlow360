-- E04 (Quỳnh Kha) | 4.2 Phân tích doanh thu | Doanh thu, số đơn, AOV theo tháng (chỉ đơn hợp lệ)
select
    year,
    month,
    month_name,
    sum(revenue)                                   as revenue,
    count(distinct order_id)                       as order_count,
    round(sum(revenue) / count(distinct order_id), 2) as avg_order_value
from mart_sales
where is_valid_sale
group by year, month, month_name
order by year, month;
