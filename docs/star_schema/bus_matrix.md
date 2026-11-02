# CommerceFlow 360 — Bus Matrix và grain tầng Gold

## Mục đích

Tài liệu này xác định grain của bốn fact và các dimension dùng chung trong Star Schema tầng Gold. Bus Matrix là cơ sở để triển khai các model dbt, kiểm thử và các Data Mart Sales, Delivery, Customer.

## Grain của các fact

| Fact | Grain — một dòng đại diện cho | Khóa định danh ở grain | Các measure chính |
|---|---|---|---|
| `fact_orders` | Một đơn hàng Olist | `order_id` | `order_count`, `delivery_days`, `days_late`; `is_delivered_late` là chỉ báo |
| `fact_order_items` | Một dòng sản phẩm trong một đơn hàng | `(order_id, order_item_id)` | `item_price`, `freight_value`, `item_count` |
| `fact_payments` | Một dòng thanh toán của một đơn hàng | `(order_id, payment_sequential)` | `payment_value` |
| `fact_reviews` | Một review Olist | `review_id` | `review_score`; `has_comment` là chỉ báo |

`order_id` được giữ trong các fact chi tiết để truy vết về đơn hàng. Đây không phải lý do để nối trực tiếp các fact với nhau: một đơn hàng có thể có nhiều dòng sản phẩm, nhiều dòng thanh toán và nhiều review.

## Bus Matrix

`X` cho biết fact có thể phân tích theo dimension. Với `dim_date` và `dim_geography`, vai trò cụ thể được liệt kê trong ô để tránh hiểu nhầm rằng một fact chỉ có một khóa tới dimension đó.

| Fact | `dim_customer` | `dim_product` | `dim_seller` | `dim_date` | `dim_geography` |
|---|---|---|---|---|---|
| `fact_orders` | Khách hàng của đơn | — | — | Ngày mua, duyệt, giao cho hãng vận chuyển, giao khách, ngày giao dự kiến | Địa lý khách hàng |
| `fact_order_items` | Khách hàng của đơn | Sản phẩm của dòng hàng | Người bán của dòng hàng | Ngày mua; hạn giao hàng của dòng hàng | Địa lý khách hàng và địa lý người bán |
| `fact_payments` | Khách hàng của đơn | — | — | Ngày mua của đơn liên quan | Địa lý khách hàng |
| `fact_reviews` | Khách hàng của đơn được đánh giá | — | — | Ngày mua (nếu dùng); ngày tạo review; ngày trả lời review | Địa lý khách hàng |

## Vai trò và quy tắc ánh xạ dimension

- **Customer:** `dim_customer` có một dòng cho mỗi `customer_unique_id` và khóa thay thế `customer_key`. Từ fact, ánh xạ qua `customer_id` của đơn hàng sang `customer_unique_id`; giữ `source_customer_id` nếu cần truy vết. Không dùng `customer_id` để đếm khách quay lại.
- **Product và Seller:** chỉ gắn với `fact_order_items`, vì nguồn xác định sản phẩm và người bán tại grain dòng hàng.
- **Date:** `dim_date` là role-playing dimension, được tham chiếu nhiều lần bằng các khóa như `purchase_date_key`, `delivered_date_key` và `review_creation_date_key`. Ngày không có trong nguồn được để khóa NULL hoặc ánh xạ tới một dòng Unknown thống nhất theo quyết định triển khai; không được tự gán một ngày thật.
- **Payment date:** dữ liệu Olist không cung cấp ngày thanh toán. `fact_payments.purchase_date_key`, nếu dùng, là ngày mua của đơn liên quan, không phải ngày thanh toán.
- **Geography:** `dim_geography` dự kiến có grain một dòng cho mỗi ZIP prefix đã chuẩn hóa. Vì nguồn geolocation có nhiều bản ghi cho cùng ZIP prefix, cần quy tắc xác định để tạo một vị trí đại diện. Địa lý khách hàng/người bán được xác định theo thông tin địa chỉ của giao dịch.
- **Các dimension còn lại:** `dim_product`, `dim_seller` và `dim_geography` dùng khóa thay thế; các mã nguồn như `product_id`, `seller_id` và ZIP prefix được giữ làm natural key để tra cứu.

## Quy tắc bảo toàn grain và KPI

1. Không nối trực tiếp `fact_orders`, `fact_order_items`, `fact_payments` và `fact_reviews` với nhau ở grain chi tiết.
2. Khi cần kết hợp số liệu từ nhiều fact, tổng hợp từng fact về grain phân tích chung (thường là `order_id`, tháng hoặc nhóm dimension) trước, rồi mới kết hợp kết quả.
3. Phân biệt `item_price` (giá sản phẩm), `freight_value` (phí vận chuyển) và `payment_value` (giá trị dòng thanh toán). Không xem chúng là cùng một measure hoặc cộng sau một phép join có thể nhân bản dòng.
4. `order_count` và `item_count` là measure đếm cộng được ở grain tương ứng; chỉ cộng `order_count` sau khi bảo đảm mỗi đơn hàng chỉ xuất hiện một lần trong tập dữ liệu đang tổng hợp.
5. Quy tắc xử lý NULL, trạng thái đơn chưa giao, khóa Unknown và cách tính giao trễ phải được triển khai nhất quán, kiểm thử và đối soát với các tầng trước.

## Quan hệ với sơ đồ

Sơ đồ Star Schema tương ứng được lưu tại [`StarSchema_CommerceFlow360.png`](./StarSchema_CommerceFlow360.png). Grain và vai trò dimension trong tài liệu này là hợp đồng thiết kế để đối chiếu khi triển khai các model Gold; nếu cấu trúc Silver thực tế khác, cần cập nhật đồng bộ sơ đồ, Bus Matrix và model thay vì âm thầm đổi grain.
