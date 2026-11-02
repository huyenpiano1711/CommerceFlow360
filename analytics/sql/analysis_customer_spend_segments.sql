-- E04 (Quỳnh Kha) | 4.4 Phân tích khách hàng | Phân khúc khách hàng theo tổng chi tiêu (quartile)
with ranked as (
    select
        total_spend,
        ntile(4) over (order by total_spend) as spend_quartile
    from mart_customer
    where total_spend > 0
)
select
    spend_quartile,
    count(*)                        as customer_count,
    min(total_spend)                as min_spend,
    max(total_spend)                as max_spend,
    round(sum(total_spend), 2)      as total_spend_segment,
    round(100.0 * sum(total_spend) / sum(sum(total_spend)) over (), 2) as pct_revenue
from ranked
group by spend_quartile
order by spend_quartile;
