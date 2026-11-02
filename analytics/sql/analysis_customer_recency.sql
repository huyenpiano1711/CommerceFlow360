-- E04 (Quỳnh Kha) | 4.4 Phân tích khách hàng | Phân bố thời gian từ lần mua gần nhất (recency, ngày)
-- Mốc so sánh = ngày đặt hàng lớn nhất toàn dữ liệu (snapshot_date trong mart_customer.sql).
select
    case
        when days_since_last_order <= 90  then '0-90 ngay'
        when days_since_last_order <= 180 then '91-180 ngay'
        when days_since_last_order <= 365 then '181-365 ngay'
        else '> 365 ngay'
    end                                          as nhom_recency,
    count(*)                                     as customer_count,
    round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_customers
from mart_customer
where has_valid_order  -- [Sửa logic] khách không có đơn hợp lệ có recency NULL, trước đây rơi vào nhóm '> 365 ngay'
group by 1
order by min(days_since_last_order);
