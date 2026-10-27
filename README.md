# CommerceFlow 360

## Mục tiêu

CommerceFlow 360 là đồ án môn **Nhà kho dữ liệu và Tích hợp**, xây dựng kho dữ liệu tích hợp để phân tích hiệu quả kinh doanh, vận hành đơn hàng và hành vi khách hàng trong thương mại điện tử. Kiến trúc mục tiêu là:

`Olist CSV + Brazil Holidays → Bronze → Silver → Gold → Data Mart → Streamlit`

Phạm vi hiện tại chỉ gồm **A01 – chuẩn bị repository** và **A02 – chuẩn bị, kiểm tra dữ liệu nguồn**. Các tầng Bronze/Silver/Gold, data mart và dashboard chưa được triển khai.

## Nguồn dữ liệu

- Tên: **Brazilian E-Commerce Public Dataset by Olist**.
- Đơn vị công bố: **Olist**.
- Nguồn: [Kaggle – Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
- Phạm vi thời gian được mô tả bởi nguồn: các đơn hàng từ năm 2016 đến 2018 tại Brazil.
- Thành phần sử dụng: 9 CSV Olist nguyên bản trong `data/raw/`.
- Ngày kiểm tra nguồn: **2026-10-27**.
- Giấy phép: **chưa xác minh độc lập từ metadata có thể truy cập trong môi trường thực thi hiện tại**. Người sử dụng cần kiểm tra mục License trên trang Kaggle trước khi phân phối lại hoặc dùng ngoài phạm vi học tập.

Dữ liệu ngày lễ quốc gia Brazil 2016–2018 được sinh bằng thư viện Python `holidays`; phiên bản thư viện được ghi trong `data/reference/holidays_brazil_metadata.json` khi chạy script.

## Công nghệ

Python, Pandas, NumPy, DuckDB, dbt Core (`dbt-duckdb`), Google Colab, `holidays`, KaggleHub, PyArrow, Matplotlib, Plotly, Streamlit và pytest.

## Cấu trúc repository

```text
CommerceFlow360/
├── app/                    # Ứng dụng Streamlit (giai đoạn sau)
├── data/
│   ├── raw/                # 9 CSV Olist và holidays_brazil.csv
│   ├── reference/          # Metadata/nguồn tham chiếu
│   ├── profiling/          # Báo cáo kiểm tra dữ liệu nguồn
│   └── exports/            # Dữ liệu xuất tạm (không commit)
├── dbt_project/            # Khung dự án dbt cho các giai đoạn sau
├── docs/                   # Kiến trúc, data dictionary, data quality
├── notebooks/              # Notebook chạy trên local/Google Colab
├── reports/                # Hình và bảng báo cáo
├── slides/                 # Slide đồ án
├── src/
│   ├── ingestion/          # Tạo/thu nhận dữ liệu nguồn
│   ├── validation/         # Profiling và kiểm tra dữ liệu
│   ├── pipeline/           # Pipeline (giai đoạn sau)
│   └── utils/              # Tiện ích dùng chung
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Các thư mục trống có `.gitkeep` để Git theo dõi. Chưa tạo notebook `00_Project_Setup.ipynb` vì chưa có nội dung nghiệp vụ thực tế.

## Cài đặt trên Windows

Yêu cầu Python 3.10 trở lên và Git.

```powershell
git clone https://github.com/huyenpiano1711/CommerceFlow360.git
cd CommerceFlow360
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Chạy A02 từ repository root:

```powershell
python src\validation\profile_raw_data.py
python src\ingestion\generate_brazil_holidays.py
```

## Chạy trên Google Colab

Không sử dụng Google Drive. Trong một notebook Colab mới:

```python
!git clone https://github.com/huyenpiano1711/CommerceFlow360.git
%cd CommerceFlow360
!python -m pip install -r requirements.txt
```

Sau đó mở/chạy `notebooks/01_Data_Source_Setup.ipynb`, hoặc chạy trực tiếp hai script như phần Windows. Với repository private, dùng tính năng Secrets của Colab và phương thức xác thực GitHub ngắn hạn; không ghi token vào notebook, URL clone, output hay repository.

Colab có phiên làm việc tạm thời: file cục bộ, bao gồm database DuckDB, có thể mất khi runtime kết thúc. Hãy tải artifact cần giữ về máy hoặc commit một artifact phù hợp sau khi đã kiểm tra kích thước và dữ liệu nhạy cảm. Không đặt database DuckDB trên Google Drive trong pipeline này.

## Lấy dữ liệu Olist

Repository hiện lưu 9 CSV Olist trong `data/raw/`. Script không tải lại hay ghi đè nếu chúng đã đủ. Nếu thiếu file, notebook A02 cung cấp cell tùy chọn dùng `kagglehub` để tải dataset và chỉ sao chép file còn thiếu. Kaggle có thể yêu cầu tài khoản/quyền truy cập; dùng Kaggle credentials qua biến môi trường hoặc cơ chế secrets, không hardcode khóa.

## Chạy notebook A02

1. Clone repository và cài dependencies.
2. Mở `notebooks/01_Data_Source_Setup.ipynb` từ repository root (hoặc upload notebook lên Colab sau khi clone).
3. Chạy lần lượt các cell.
4. Kiểm tra bảng danh sách 9 CSV, báo cáo `doi_chieu_so_dong.csv`, báo cáo missing/duplicate và bảng ngày lễ.
5. Cell cuối chỉ PASS khi các output bắt buộc và các điều kiện dữ liệu đều đạt.

## Quy tắc làm việc với GitHub

- Tạo branch theo task, ví dụ `feature/a02-data-source-setup`; không làm việc dài hạn trực tiếp trên `main`.
- Pull/rebase thay đổi mới trước khi bắt đầu, commit nhỏ với thông điệp rõ ràng và tạo pull request để review.
- Không commit `.env`, token, virtual environment, cache, log, DuckDB hoặc output trung gian lớn.
- `data/raw/*.csv` được chủ đích lưu trong repository. Phải kiểm tra giới hạn kích thước GitHub trước khi thêm file mới; không tự bật Git LFS cho toàn bộ CSV.
- Không chỉnh sửa nội dung 9 CSV gốc. Mọi dữ liệu dẫn xuất phải nằm ngoài `data/raw/` (ngoại trừ file ngày lễ được sinh có kiểm soát).

## Lưu ý kích thước dữ liệu

`olist_geolocation_dataset.csv` khoảng 59 MiB: thấp hơn giới hạn cứng 100 MiB/file của GitHub nhưng cao hơn mức 50 MiB mà GitHub khuyến nghị. Repository hiện chưa dùng Git LFS; cần theo dõi quota và chỉ cân nhắc LFS khi chính sách nhóm thay đổi.
