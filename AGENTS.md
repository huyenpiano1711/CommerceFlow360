# AGENTS.md — Hướng dẫn chạy CommerceFlow 360 cho AI agent

Tài liệu này dành cho AI agent (và người) cần **chạy lại toàn bộ pipeline** của đồ án.
Làm đúng thứ tự, kiểm tra kết quả sau mỗi bước, dừng lại và báo cáo nếu kết quả khác mục "Kết quả đúng".

## 1. Bối cảnh dự án

- Kho dữ liệu thương mại điện tử Olist (Brazil 2016–2018) theo kiến trúc Medallion:
  `data/raw/*.csv → Bronze → Silver → Gold (Star Schema) → Data Mart → Parquet → Streamlit`.
- Kho dữ liệu là **một file DuckDB**: `commerceflow.duckdb` ở thư mục gốc repo (không commit lên Git).
- Biến đổi Silver/Gold/Mart viết bằng **dbt Core + dbt-duckdb** trong `dbt_project/`.
- Mọi bảng nằm trong schema `main`, phân biệt tầng bằng tiền tố: `bronze_`, `silver_`, `dim_`, `fact_`, `mart_`.

## 2. Quy tắc bắt buộc (KHÔNG vi phạm)

1. **Không sửa, xóa, đổi tên** bất kỳ file nào trong `data/raw/` (dữ liệu gốc).
2. Không đổi tên file/bảng/model đã thống nhất (xem sheet "Quy tắc đặt tên" trong PCCV).
3. Không tự điền số liệu mẫu vào báo cáo/dashboard; mọi số phải lấy từ kết quả chạy code.
4. Không commit `commerceflow.duckdb`, `.venv/`, `dbt_project/target/`.
5. Chỉ một tiến trình được **ghi** vào `commerceflow.duckdb` tại một thời điểm.
   Khi chỉ đọc, luôn mở với `duckdb.connect(path, read_only=True)`.
6. Không push lên `main` trực tiếp; làm trên nhánh rồi mở Pull Request.
7. Commit message theo mẫu: `[CODE] <nội dung>` hoặc `[BÁO CÁO] <nội dung>`.

## 3. Yêu cầu môi trường

- Python **3.12 hoặc 3.13** (đã kiểm chứng với dbt-core 1.12 + dbt-duckdb 1.11).
- Thư viện trong `requirements.txt` (dbt-core và dbt-duckdb ≥ 1.10 là bắt buộc vì `schema.yml` dùng cú pháp `data_tests` + `arguments`).
- Luôn đứng ở **thư mục gốc repo** khi chạy lệnh (thư mục chứa `requirements.txt`).

## 4. Cài đặt lần đầu

### Windows (PowerShell)

```powershell
cd D:\CommerceFlow360
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt ipykernel

New-Item -ItemType Directory -Force "$env:USERPROFILE\.dbt" | Out-Null
Copy-Item dbt_project\profiles.yml.example "$env:USERPROFILE\.dbt\profiles.yml" -Force
```

Nếu `Activate.ps1` báo *running scripts is disabled*: chạy `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` rồi kích hoạt lại.

### Linux / macOS / Google Colab

```bash
python -m venv .venv && source .venv/bin/activate      # Colab: bỏ dòng này
pip install -r requirements.txt ipykernel
mkdir -p ~/.dbt && cp dbt_project/profiles.yml.example ~/.dbt/profiles.yml
```

Colab: clone trước bằng
`git clone https://github.com/huyenpiano1711/CommerceFlow360.git /content/CommerceFlow360 && cd /content/CommerceFlow360`.

### Kiểm tra cài đặt

```powershell
python -c "import duckdb, dbt, pandas; print('ok', duckdb.__version__)"
cd dbt_project; dbt debug; cd ..
```

Kết quả đúng: in `ok ...` và `dbt debug` kết thúc bằng `All checks passed!`.

> Mỗi terminal mới phải kích hoạt lại môi trường (`.\.venv\Scripts\Activate.ps1`).
> Dấu nhắc đúng có tiền tố `(.venv)`. Lỗi `No module named 'duckdb'` = quên kích hoạt.

## 5. Chạy toàn bộ pipeline (cách chính — 3 lệnh)

Chạy tuần tự từ thư mục gốc repo:

| # | Lệnh | Task | Việc làm |
|---|------|------|----------|
| 1 | `python scripts/load_bronze.py` | B01 | Nạp 10 CSV vào `bronze_*` (giữ chuỗi gốc, thêm `_ingested_at`, `_source_file`), ghi `ingestion_log`, đối chiếu số dòng với CSV |
| 2 | `python scripts/export_parquet.py` | C, D, E01–E03, E05 | `dbt build` toàn bộ (Silver → Gold → Mart + tất cả test), sau đó xuất 4 file Parquet. **Tự dừng nếu dbt có lỗi hoặc test FAIL** |
| 3 | `python scripts/run_e04_analytics.py` | E04 | Chạy 10 truy vấn `analytics/sql/*.sql`, xuất `reports/tables/Bang_4.x_*.csv` (kèm Bảng 4.1.1 tóm tắt kiểm thử từ `quality_results.parquet`) và `reports/figures/Hinh_4.x_*.png` |

Trên Windows có thể dùng `\` thay `/` trong đường dẫn.

### Kết quả đúng

- Lệnh 1: in 10 dòng, cột `status` đều `PASS`. Số dòng tham chiếu:

  | Bảng | Số dòng |
  |---|---|
  | bronze_customers | 99441 |
  | bronze_geolocation | 1000163 |
  | bronze_order_items | 112650 |
  | bronze_order_payments | 103886 |
  | bronze_order_reviews | 99224 |
  | bronze_orders | 99441 |
  | bronze_products | 32951 |
  | bronze_sellers | 3095 |
  | bronze_product_category_name_translation | 71 |
  | bronze_holidays | 27 |

- Lệnh 2: có dòng `Done. PASS=106 WARN=5 ERROR=0` (22 model + 89 test) và 4 dòng xuất file:
  `mart_sales: 112650 dong`, `mart_delivery: 100010 dong`, `mart_customer: 96096 dong`, `quality_results: 89 test`.
  5 WARN là bất thường có thật của dữ liệu nguồn đã được gắn cờ ở Silver — **không phải lỗi**:
  `not_null_silver_sellers_seller_city` (2), `test_silver_carrier_after_purchase` (166),
  `test_silver_review_after_purchase` (64), `not_null_silver_geolocation_geolocation_lat` (5),
  `test_silver_geolocation_customer_coverage` (285).
- Lệnh 3: dòng cuối `Hoan tat E04.`

### Số liệu đối soát phải khớp giữa Bronze, Silver, Gold

| Chỉ số | Giá trị |
|---|---|
| Số đơn | 99441 |
| Tổng `price` (item_revenue) | 13591643.70 |
| Tổng `freight_value` | 2251909.54 |
| Tổng `payment_value` | 16008872.12 |

Nếu khác các số trên → báo lỗi, không sửa số cho khớp.

## 6. Chạy bằng notebook (khi cần ảnh minh chứng cho báo cáo)

Kernel: chọn **Python Environments… → `.venv`** (không chọn "Existing Jupyter Server").
Chạy **Run All** theo đúng thứ tự:

| Thứ tự | Notebook | Task | Đầu ra chính |
|---|---|---|---|
| (tùy chọn) | `notebooks/01_Data_Source_Setup.ipynb` | A02 | `data/profiling/*.csv`, `data/raw/holidays_brazil.csv` |
| 1 | `notebooks/02_Bronze_Ingestion.ipynb` | B01 | `bronze_*`, `ingestion_log`, `reports/tables/Bang_3.3.1_NhatKyNapBronze.csv` |
| 2 | `notebooks/03_Silver_Transformation.ipynb` | C01–C03 | `silver_*` + 70 test Silver, `reports/tables/Bang_3.4.*.csv`, `reports/figures/Hinh_3.4.1_LuongXuLySilver.png`, `docs/data_quality/silver_test_results.csv` |
| 3 | `notebooks/04_Gold_Data_Warehouse.ipynb` | D02–D03 | 5 `dim_*`, 4 `fact_*` (chỉ build, test ở notebook 05) |
| 4 | `notebooks/05_Data_Quality.ipynb` | D04 | 3 test Gold, `reports/tables/Bang_3.7.1_DoiSoatGold.csv` |
| 5 | `notebooks/06_Business_Analytics.ipynb` | E01–E05 | `dbt build` toàn bộ + `data/exports/*.parquet` (giống lệnh 2), bảng/hình Chương 4 (giống lệnh 3) |

Notebook 06 đã gồm bước xuất Parquet, không cần chạy thêm script.
Notebook 01 ghi lại `data/raw/holidays_brazil.csv`; chỉ chạy khi thật sự cần sinh lại dữ liệu nguồn.

## 7. Chạy một phần dbt

Chạy trong thư mục `dbt_project/`:

```powershell
$env:PYTHONUTF8 = "1"
cd dbt_project
dbt build --select silver --exclude test_sales_reconciliation   # Silver + test Silver
dbt build --select gold            # Gold + Mart + test liên quan
dbt build --select mart_customer   # một model cụ thể
dbt build --select +mart_sales     # mart_sales và mọi model phía trước nó
dbt test                           # chỉ chạy lại test
cd ..
```

`--select silver` mặc định kéo theo cả `test_sales_reconciliation` (đối soát tới Gold), nên phải `--exclude` khi Gold chưa build.

## 8. Bản đồ thư mục quan trọng

| Đường dẫn | Nội dung |
|---|---|
| `data/raw/` | 9 CSV Olist + `holidays_brazil.csv` (CHỈ ĐỌC) |
| `src/ingestion/bronze_ingestion.py` | Logic nạp Bronze dùng chung |
| `src/utils/project.py` | Đường dẫn, `DUCKDB_PATH`, `run_dbt`, `query`, đọc kết quả test dbt — dùng chung cho script và notebook |
| `src/reporting/` | `exports.py` (E05 Parquet), `kpi_report.py` (E04 bảng/hình Chương 4), `silver_flow.py` (Hình 3.4.1) |
| `dbt_project/models/sources.yml` | Khai báo 10 bảng `bronze_*` |
| `dbt_project/models/silver/` | 10 model `silver_*` + `schema.yml` |
| `dbt_project/models/gold/dimensions/` | `dim_customer`, `dim_product`, `dim_seller`, `dim_date`, `dim_geography` |
| `dbt_project/models/gold/facts/` | `fact_orders`, `fact_order_items`, `fact_payments`, `fact_reviews` |
| `dbt_project/models/gold/marts/` | `mart_sales`, `mart_delivery`, `mart_customer` + `schema.yml` |
| `dbt_project/tests/` | Test tùy chỉnh `test_silver_*`, `test_gold_*`, `test_sales_reconciliation`, `test_mart_reconciliation` |
| `dbt_project/macros/` | Macro làm sạch dùng chung, test `unique_combination` |
| `analytics/sql/` | 10 truy vấn KPI `analysis_<mart>_<nội dung>.sql` |
| `scripts/` | `load_bronze.py`, `export_parquet.py`, `run_e04_analytics.py` (chỉ gọi hàm trong `src/`) |
| `data/exports/` | `mart_*.parquet`, `quality_results.parquet` (đầu vào dashboard) |
| `reports/tables/`, `reports/figures/` | Bảng, hình cho báo cáo |
| `docs/star_schema/` | Sơ đồ Star Schema, `bus_matrix.md` (grain các fact) |

## 9. Quy tắc nghiệp vụ đã chốt (giữ nguyên khi sửa code)

- **Grain:** `fact_orders` = 1 đơn; `fact_order_items` = (order_id, order_item_id);
  `fact_payments` = (order_id, payment_sequential); `fact_reviews` = (review_id, order_id).
  Không join trực tiếp các fact với nhau ở grain chi tiết; tổng hợp về cùng grain trước.
- **Đơn hợp lệ:** `fact_orders.is_valid_order` = trạng thái không phải `canceled`, `unavailable`.
  Mọi mart dùng cờ này, không tự định nghĩa lại.
- **Doanh thu** (`mart_sales.revenue`) = `price` của dòng hàng, chỉ tính khi `is_valid_sale`.
  `freight_value` và `payment_value` là measure riêng, không cộng lẫn.
- **Số đơn** = `count(distinct order_id)`; không cộng số đơn giữa các danh mục/người bán.
- **Giao trễ:** chỉ tính cho đơn `delivered` có ngày nhận; so sánh theo **ngày**
  (`delivered_date > estimated_date`).
- **Đánh giá:** khi gắn vào đơn, chỉ lấy `is_latest_review = true`.
- **Khách hàng:** dùng `customer_unique_id` (khóa `dim_customer`) cho khách quay lại/tổng chi tiêu;
  `customer_id` chỉ là mã theo từng đơn. Các chỉ số khách hàng chỉ tính trên đơn hợp lệ;
  lọc `has_valid_order` khi tính tỷ lệ mua lại, recency, phân khúc.
- **Recency** tính đến ngày đặt hàng lớn nhất trong dữ liệu, không phải ngày hiện tại.

## 10. Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `No module named 'duckdb'` / `'dbt'` | Chưa kích hoạt `.venv` hoặc chưa cài | Kích hoạt `.venv`, chạy lại `pip install -r requirements.txt` |
| `Could not find profile named 'commerceflow360'` | Chưa chép `profiles.yml` | Làm lại bước chép `profiles.yml.example` ở mục 4 |
| `Table with name bronze_... does not exist` | Chưa nạp Bronze, hoặc đứng sai thư mục nên DuckDB tạo file rỗng mới | `cd` về thư mục gốc repo, chạy `python scripts/load_bronze.py` |
| `Could not set lock on file ... commerceflow.duckdb` | Notebook/tiến trình khác đang mở file ở chế độ ghi | Dừng kernel notebook hoặc tiến trình đó rồi chạy lại |
| `Không tìm thấy lệnh dbt` | `dbt` không có trong PATH và không nằm cạnh Python đang chạy | Kích hoạt `.venv`, hoặc đặt biến môi trường `DBT_EXECUTABLE` trỏ tới file dbt |
| `'charmap' codec can't decode` khi chạy `dbt` tay trên Windows | dbt đọc YAML tiếng Việt bằng bảng mã hệ thống | Đặt `$env:PYTHONUTF8 = "1"` trước khi chạy (script/notebook đã tự đặt) |
| `dbt build loi ... KHONG xuat Parquet` | Có model lỗi hoặc test FAIL | Đọc log dbt, sửa nguyên nhân gốc; không hạ test xuống `warn` để cho qua |
| Lỗi cú pháp `data_tests`/`arguments` trong `schema.yml` | dbt < 1.10 | `pip install "dbt-core>=1.10,<2" "dbt-duckdb>=1.10,<2"` |

## 11. Chạy dashboard và phần chưa làm

- Chạy dashboard từ thư mục gốc sau khi có đủ 4 file trong `data/exports/`: `streamlit run app/Home.py`.
- Dashboard chỉ đọc Parquet; nếu báo thiếu file, chạy `python scripts/export_parquet.py` trước.
- B02 `01_Data_Profiling_EDA.ipynb` + `reports/figures/Hinh_2.x_*.png`.
- G01 `07_Run_Full_Pipeline.ipynb` (có thể gọi `src.ingestion.bronze_ingestion.run`, `src.reporting.exports.build_and_export`, `src.reporting.kpi_report.run_all`).
