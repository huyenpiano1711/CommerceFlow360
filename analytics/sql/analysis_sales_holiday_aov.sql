-- E04 (Quỳnh Kha) | 4.2 Phân tích doanh thu | AOV ngày lễ Brazil so với ngày thường
select
    is_holiday,
    sum(revenue)                                     as revenue,
    count(distinct order_id)                         as order_count,
    round(sum(revenue) / count(distinct order_id), 2) as avg_order_value
from mart_sales
where is_valid_sale
group by is_holiday
order by is_holiday desc;
