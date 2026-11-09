# dbt_project – CommerceFlow 360

dbt Core + `dbt-duckdb` biến đổi dữ liệu từ `bronze_*` sang `silver_*` → `dim_*`/`fact_*` → `mart_*` trong một file DuckDB (`commerceflow.duckdb`, schema `main`).

## Cấu trúc

```text
dbt_project/
├── dbt_project.yml            # cấu hình project (C01)
├── profiles.yml.example       # mẫu kết nối DuckDB, KHÔNG commit profiles.yml thật (C01)
├── macros/
│   ├── silver_cleaning.sql    # macro làm sạch dùng chung cho Silver (C02)
│   └── test_unique_combination.sql  # generic test khóa nhiều cột (C03)
├── models/
│   ├── sources.yml            # khai báo 10 bảng bronze_* (C01)
│   ├── silver/                # 9 model silver_* + silver_holidays, schema.yml (C02, C03)
│   └── gold/                  # dimensions/, facts/, marts/ (D02, D03, E01–E03)
└── tests/                     # test_<tầng>_<nội dung>.sql (C03, D04)
```

## Chạy nhanh

Cách chính: `python scripts/export_parquet.py` từ thư mục gốc (dbt build toàn bộ, xem `AGENTS.md`).
Theo từng tầng: notebook `03_Silver_Transformation`, `04_Gold_Data_Warehouse`, `05_Data_Quality`, `06_Business_Analytics`.

Chạy tay (từ thư mục gốc repository, đã có `commerceflow.duckdb` chứa `bronze_*`):

```bash
pip install "dbt-core>=1.10,<2.0" "dbt-duckdb>=1.10,<2.0"
mkdir -p ~/.dbt && cp dbt_project/profiles.yml.example ~/.dbt/profiles.yml
export DUCKDB_PATH="$(pwd)/commerceflow.duckdb" PYTHONUTF8=1   # PowerShell: $env:DUCKDB_PATH = "$PWD\commerceflow.duckdb"; $env:PYTHONUTF8 = "1"
cd dbt_project
dbt debug
dbt run  --select silver
dbt test --select silver --exclude test_sales_reconciliation   # test này cần tầng Gold
dbt build                                                     # toàn bộ Silver -> Gold -> Mart + test
```

## Tầng Silver (C02)

| Model | Grain | Xử lý chính |
|---|---|---|
| `silver_orders` | order_id | ép kiểu 5 mốc thời gian, chuẩn hóa `order_status`, thêm `order_purchase_date`, cờ bất thường ngày giao |
| `silver_order_items` | order_id + order_item_id | `price`, `freight_value` → DECIMAL(12,2), `item_total_value` |
| `silver_order_payments` | order_id + payment_sequential | chuẩn hóa `payment_type`, số kỳ trả góp 0 → 1 (có cờ), cờ thanh toán 0 |
| `silver_order_reviews` | review_id + order_id | làm sạch bình luận, sửa mốc thời gian sai định dạng, `is_latest_review` |
| `silver_customers` | customer_id | ZIP 5 ký tự (khôi phục số 0 đầu), chuẩn hóa thành phố/bang, giữ `customer_unique_id` |
| `silver_sellers` | seller_id | ZIP 5 ký tự, chuẩn hóa tên thành phố nhập tự do |
| `silver_products` | product_id | sửa tên cột `_lenght`, danh mục NULL → `sem_categoria`, kích thước ≤ 0 → NULL, gắn tên tiếng Anh |
| `silver_product_category_name_translation` | product_category_name | 71 bản dịch gốc + 2 danh mục thiếu bản dịch + `sem_categoria` |
| `silver_geolocation` | geolocation_zip_code_prefix | gộp ~1 triệu dòng về 1 dòng/ZIP: trung vị tọa độ trong lãnh thổ Brazil, bang/thành phố phổ biến nhất |
| `silver_holidays` | holiday_date | bảng hỗ trợ cho `dim_date` (Gold không đọc trực tiếp Bronze) |

Silver **không xóa** bản ghi hợp lệ về nghiệp vụ: bất thường được giữ nguyên và đánh dấu bằng cột `flag_*` để Gold/Data Mart quyết định loại trừ khi tính KPI.

### Lưu ý cho tầng Gold

- `dim_customer`: dùng `customer_unique_id`; nối đơn hàng qua `silver_orders.customer_id → silver_customers.customer_id`.
- `fact_reviews` / phân tích 1 đánh giá mỗi đơn: lọc `is_latest_review = true`.
- `dim_geography`: 285 khách hàng/người bán có ZIP không có trong `silver_geolocation` → đã bổ sung city/state từ địa chỉ khách hàng/người bán (`location_source`).
- `dim_date`: lấy cờ ngày lễ từ `silver_holidays`.
- Tiền tệ đã là DECIMAL(12,2), cộng dồn khớp tuyệt đối với Bronze.

## Kiểm thử (C03)

`dbt test --select silver` chạy 70 test: unique, not_null, accepted_values, relationships, khóa nhiều cột và 6 test tùy chỉnh
(`tests/test_silver_*.sql`). Test mức `warn` ghi nhận bất thường thật của dữ liệu nguồn, không chặn pipeline.
Kết quả lần chạy gần nhất: `docs/data_quality/silver_test_results.csv`.

## Tầng Gold và kiểm thử (D02–D04, E01–E03)

- `models/gold/dimensions/`: `dim_customer`, `dim_product`, `dim_seller`, `dim_date`, `dim_geography`.
- `models/gold/facts/`: `fact_orders`, `fact_order_items`, `fact_payments`, `fact_reviews` (grain: `docs/star_schema/bus_matrix.md`).
- `models/gold/marts/`: `mart_sales`, `mart_delivery`, `mart_customer` + `schema.yml`.
- Test Gold: `test_gold_fact_grain`, `test_gold_dimension_relationships`, `test_sales_reconciliation` (Bronze → Silver → Gold),
  `test_mart_reconciliation` (Gold → Mart). `dbt build` toàn bộ: 22 model + 91 test, kết quả mong đợi `PASS=108 WARN=5 ERROR=0`.
