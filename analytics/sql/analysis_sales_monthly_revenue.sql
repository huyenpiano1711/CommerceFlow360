-- E04 (Quỳnh Kha) | 4.2 Phân tích doanh thu | Doanh thu, số đơn, AOV theo tháng (chỉ đơn hợp lệ)
-- Chỉ lấy các tháng đầy đủ 2017-01 -> 2018-08 (trùng FULL_MONTH_START/END của dashboard):
-- 09-12/2016 là giai đoạn khởi động (vài đơn) và 09/2018 bị cắt khi trích xuất (1 đơn), không so sánh được.
select
    year,
    month,
    month_name,
    sum(revenue)                                   as revenue,
    count(distinct order_id)                       as order_count,
    round(sum(revenue) / count(distinct order_id), 2) as avg_order_value
from mart_sales
where is_valid_sale
  and order_purchase_date between date '2017-01-01' and date '2018-08-31'
group by year, month, month_name
order by year, month;
