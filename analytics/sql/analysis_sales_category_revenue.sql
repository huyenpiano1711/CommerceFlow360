-- E04 (Quỳnh Kha) | 4.2 Phân tích doanh thu | Top 10 danh mục sản phẩm theo doanh thu
select
    coalesce(product_category, 'unknown')          as product_category,
    sum(revenue)                                   as revenue,
    count(distinct order_id)                       as order_count
from mart_sales
where is_valid_sale
group by product_category
order by revenue desc
limit 10;
