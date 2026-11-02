-- E04 (Quỳnh Kha) | 4.4 Phân tích khách hàng | Tỷ lệ khách mua 1 lần vs mua lại (customer_unique_id)
select
    case when is_repeat_customer then 'mua lại (>=2 đơn)' else 'mua 1 lần' end as nhom_khach_hang,
    count(*)                                             as customer_count,
    round(100.0 * count(*) / sum(count(*)) over (), 2)   as pct_customers,
    round(avg(total_spend), 2)                           as avg_total_spend
from mart_customer
group by is_repeat_customer
order by is_repeat_customer desc;
