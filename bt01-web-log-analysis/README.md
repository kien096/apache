# BT01 - Phân tích log web quy mô lớn

Project này được tách riêng để bám đúng yêu cầu BT01: `HDFS`, `MapReduce`, `YARN`, `Python Streaming`, benchmark reducer và dashboard tương tác bằng `Grafana`.

## 1. Kiến trúc

Luồng dữ liệu:

```text
Apache access log
  -> HDFS /logs/yyyy/MM/dd/access.log
  -> Hadoop Streaming normalize
  -> 4 job MapReduce Python
  -> HDFS /bt01/output/*
  -> export TSV
  -> PostgreSQL
  -> Grafana dashboard
```

Các thành phần Docker:

- `bt01-namenode`: HDFS NameNode, UI `http://localhost:9871`
- `bt01-datanode1`, `bt01-datanode2`: HDFS DataNode
- `bt01-resourcemanager`: YARN ResourceManager, UI `http://localhost:8089`
- `bt01-nodemanager1`, `bt01-nodemanager2`: YARN NodeManager
- `bt01-historyserver`: MapReduce History UI `http://localhost:19889`
- `bt01-postgres`: nơi lưu kết quả để dashboard truy vấn
- `bt01-grafana`: dashboard, UI `http://localhost:3001`, tài khoản `admin/admin`

## 2. Cấu trúc thư mục

```text
bt01-web-log-analysis/
  docker-compose.yml
  docker/
    Dockerfile
    conf/
    scripts/
  data/
    generate_apache_logs.py
    raw/
  streaming/
    apache_log_parser.py
    *_mapper.py
    *_reducer.py
  scripts/
    00-start-cluster.ps1
    01-generate-logs.ps1
    02-load-logs-to-hdfs.ps1
    03-run-all-jobs.ps1
    04-benchmark-reducers.ps1
    05-export-results.ps1
    06-load-dashboard.ps1
    99-stop-cluster.ps1
  dashboard/
    postgres/init.sql
    grafana/
  docs/
    technical-report.md
    benchmark-results.csv
```

## 3. Cách chạy từ đầu

Chạy các lệnh từ thư mục `bt01-web-log-analysis`.

### Bước 1: Khởi động cụm Hadoop/YARN và dashboard

```powershell
.\scripts\00-start-cluster.ps1
```

Kiểm tra:

- HDFS UI: `http://localhost:9871`
- YARN UI: `http://localhost:8089`
- Grafana: `http://localhost:3001`

### Bước 2: Tạo dữ liệu log

Bạn có thể tạo đúng yêu cầu tối thiểu 2 triệu dòng:

```powershell
.\scripts\01-generate-logs.ps1 -Lines 2000000 -Days 3 -StartDate "2026-06-01"
```

Để test nhanh trước khi demo, có thể dùng 50.000 dòng:

```powershell
.\scripts\01-generate-logs.ps1 -Lines 50000 -Days 3 -StartDate "2026-06-01"
```

Script sinh log theo Apache Combined Log Format và đặt vào:

```text
data/raw/yyyy/MM/dd/access.log
```

Mỗi lần chạy generator, các file `*.log` cũ trong `data/raw` sẽ được xóa để số dòng đúng với tham số `-Lines`.

### Bước 3: Nạp log lên HDFS

```powershell
.\scripts\02-load-logs-to-hdfs.ps1
```

Dữ liệu trên HDFS sẽ có dạng:

```text
/logs/2026/06/01/access.log
/logs/2026/06/02/access.log
/logs/2026/06/03/access.log
```

### Bước 4: Chạy các chương trình MapReduce

```powershell
.\scripts\03-run-all-jobs.ps1
```

Script này chạy các job:

- `bt01-normalize`: chuẩn hóa log thô thành TSV
- `bt01-top-20-ips`: tìm 20 IP truy cập nhiều nhất trên toàn bộ tập log
- `bt01-ip-counts-by-day`: đếm IP theo ngày để dashboard có thể lọc tương tác
- `bt01-status-by-day`: thống kê mã HTTP theo ngày
- `bt01-top-10-urls-by-day`: tìm 10 URL được xem nhiều nhất mỗi ngày
- `bt01-traffic-by-hour`: thống kê lưu lượng theo 24 giờ

Theo dõi job trên YARN UI:

```text
http://localhost:8089
```

### Bước 5: Benchmark 1, 2, 4 reducer

```powershell
.\scripts\04-benchmark-reducers.ps1
```

Kết quả được ghi vào:

```text
docs/benchmark-results.csv
```

Dùng file này để vẽ biểu đồ so sánh tốc độ trong báo cáo. Benchmark tập trung vào `status_by_day` và `traffic_by_hour` vì hai job này phù hợp để so sánh 1, 2, 4 reducer.

### Bước 6: Export kết quả từ HDFS

```powershell
.\scripts\05-export-results.ps1
```

Kết quả TSV nằm trong:

```text
dashboard/export/
```

### Bước 7: Load kết quả vào PostgreSQL cho Grafana

```powershell
.\scripts\06-load-dashboard.ps1
```

Mở dashboard:

```text
http://localhost:3001
```

Đăng nhập:

```text
admin / admin
```

Dashboard có các phần:

- Lưu lượng truy cập theo thời gian
- Top 20 IP
- Phân bố mã HTTP theo ngày
- Top URL mỗi ngày
- Lọc theo khoảng thời gian bằng time picker của Grafana

## 4. Giải thích các chương trình MapReduce

### Normalize

File: `streaming/normalize_mapper.py`

Đọc Apache Combined Log Format, parse thành 7 cột:

```text
day hour ip method url status bytes
```

Kết quả nằm ở:

```text
/bt01/output/normalized
```

### Chương trình 1: Top 20 IP

Files cho kết quả nộp bài:

- `streaming/top_ips_global_mapper.py`
- `streaming/top_ips_global_reducer.py`

Mapper emit:

```text
ip 1
```

Reducer cộng số lần truy cập theo IP và giữ top 20 IP lớn nhất. Kết quả nằm ở:

```text
/bt01/output/top_ips_global
```

Files hỗ trợ dashboard:

- `streaming/top_ips_mapper.py`
- `streaming/top_ips_reducer.py`

Mapper emit:

```text
day ip 1
```

Reducer cộng số lần truy cập theo cặp `(day, ip)`. Dashboard sẽ tổng hợp theo khoảng ngày đang chọn và hiển thị top 20 IP.

### Chương trình 2: Mã HTTP theo ngày

Files:

- `streaming/status_by_day_mapper.py`
- `streaming/status_by_day_reducer.py`

Output:

```text
day status hits
```

### Chương trình 3: Top 10 URL mỗi ngày

Files:

- `streaming/top_urls_by_day_mapper.py`
- `streaming/top_urls_by_day_reducer.py`

Mapper emit:

```text
day url 1
```

Reducer cộng số lần truy cập URL theo ngày, giữ top 10 URL cho từng ngày.

### Chương trình 4: Lưu lượng theo 24 giờ

Files:

- `streaming/traffic_by_hour_mapper.py`
- `streaming/traffic_by_hour_reducer.py`

Output:

```text
day hour hits
```

## 5. Nối các chương trình và theo dõi YARN

Luồng chạy nằm trong `scripts/03-run-all-jobs.ps1`.

Trong triển khai này, log thô được nối qua bước `normalize`, sau đó các chương trình phân tích chạy trên cùng dữ liệu chuẩn hóa. Đây là cách đúng về kỹ thuật vì các thống kê IP, mã HTTP, URL và giờ là các nhánh phân tích độc lập. Toàn bộ job vẫn chạy bằng Hadoop Streaming trên YARN và xem được trên YARN Web UI.

Wrapper `scripts/hadoop-streaming.sh` truyền `stream.num.map.output.key.fields` để Hadoop Streaming sort/group đúng các key nhiều cột như `(day, status)`, `(day, hour)` và `(day, url)`.

## 6. Sản phẩm nộp bài

Nhóm có thể nộp:

- Code MapReduce: thư mục `streaming/`
- Script cài/chạy môi trường: `docker-compose.yml`, `docker/`, `scripts/`
- Dashboard: Grafana tại `http://localhost:3001` và file JSON trong `dashboard/grafana/dashboards/`
- Báo cáo kỹ thuật: `docs/technical-report.md`
- Benchmark: `docs/benchmark-results.csv`
- Video demo: quay các bước start cluster, load HDFS, chạy YARN job, xem dashboard

## 7. Dừng hệ thống

```powershell
.\scripts\99-stop-cluster.ps1
```

Nếu muốn xóa sạch volume Docker để chạy lại từ đầu:

```powershell
docker compose down -v
```
