# Báo Cáo Kỹ Thuật BT01 - Phân Tích Log Web Quy Mô Lớn

## 1. Thông Tin Chung

**Tên đề tài:** BT01 - Phân tích log web quy mô lớn  
**Công nghệ sử dụng:** HDFS, MapReduce, YARN, Python Streaming, PostgreSQL, Grafana  
**Dữ liệu thử nghiệm:** 2.000.000 dòng log web theo định dạng Apache Combined Log Format  

> **Chèn thông tin nhóm tại đây**
>
> - Lớp:
> - Môn học:
> - Giảng viên:
> - Thành viên nhóm:
> - Vai trò từng thành viên:

## 2. Mục Tiêu Đề Tài

Mục tiêu của đề tài là xây dựng một hệ thống xử lý log web quy mô lớn bằng các công nghệ trong hệ sinh thái Hadoop. Hệ thống cần lưu trữ log trên HDFS, xử lý dữ liệu bằng MapReduce chạy trên YARN, sau đó trực quan hóa kết quả bằng dashboard tương tác.

Cụ thể, hệ thống cần giải quyết các bài toán sau:

- Tìm 20 địa chỉ IP truy cập nhiều nhất.
- Thống kê phân bố mã trạng thái HTTP theo từng ngày.
- Tìm 10 URL được truy cập nhiều nhất mỗi ngày.
- Thống kê lưu lượng truy cập theo 24 khung giờ trong ngày.
- Chạy thử nghiệm với 1, 2, 4 reducer và so sánh thời gian xử lý.
- Hiển thị kết quả trên dashboard tương tác.

## 3. Tổng Quan Kiến Trúc Hệ Thống

Hệ thống được triển khai bằng Docker Compose, gồm các thành phần chính:

- **HDFS NameNode:** quản lý metadata của hệ thống file phân tán.
- **HDFS DataNode 1 và DataNode 2:** lưu trữ dữ liệu log phân tán.
- **YARN ResourceManager:** quản lý tài nguyên và điều phối job.
- **YARN NodeManager 1 và NodeManager 2:** thực thi các mapper/reducer.
- **Hadoop Streaming:** cho phép viết mapper/reducer bằng Python.
- **PostgreSQL:** lưu kết quả MapReduce sau khi export từ HDFS.
- **Grafana:** xây dựng dashboard tương tác từ dữ liệu trong PostgreSQL.

Luồng xử lý tổng thể:

```text
Sinh log hoặc dùng log có sẵn
  -> Nạp log vào HDFS theo /logs/yyyy/MM/dd/
  -> Chạy Hadoop Streaming trên YARN
  -> Ghi kết quả ra HDFS tại /bt01/output/
  -> Export kết quả từ HDFS ra TSV
  -> Load TSV vào PostgreSQL
  -> Grafana đọc PostgreSQL và hiển thị dashboard
```

> **[Ảnh 1 - Sơ đồ kiến trúc hệ thống]**
>
> Gợi ý chèn ảnh: vẽ sơ đồ gồm các khối `Log Generator -> HDFS -> YARN/MapReduce -> HDFS Output -> PostgreSQL -> Grafana`.

## 4. Cấu Trúc Project

Project BT01 được đặt trong thư mục:

```text
bt01-web-log-analysis/
```

Các thư mục quan trọng:

```text
bt01-web-log-analysis/
  docker-compose.yml
  docker/
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
  dashboard/
    postgres/
    grafana/
  docs/
    technical-report.md
    benchmark-results.csv
```

Ý nghĩa:

- `docker-compose.yml`: định nghĩa toàn bộ cụm Hadoop/YARN/PostgreSQL/Grafana.
- `docker/conf/`: chứa cấu hình Hadoop, HDFS, YARN, MapReduce.
- `data/generate_apache_logs.py`: sinh dữ liệu log giả lập.
- `streaming/`: chứa code mapper và reducer Python.
- `scripts/`: chứa các script chạy từng bước.
- `dashboard/`: chứa schema PostgreSQL và cấu hình Grafana.
- `docs/`: chứa báo cáo và kết quả benchmark.

## 5. Dữ Liệu Log

### 5.1 Định Dạng Log

Dữ liệu được sinh theo Apache Combined Log Format:

```text
IP - - [dd/MMM/yyyy:HH:mm:ss +0700] "METHOD URL HTTP/1.1" STATUS BYTES "REFERER" "USER_AGENT"
```

Ví dụ:

```text
10.10.3.9 - - [01/Jun/2026:08:15:01 +0700] "GET /products HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

Các trường quan trọng được dùng trong phân tích:

- `IP`: địa chỉ người truy cập.
- `time`: thời điểm truy cập.
- `URL`: trang được truy cập.
- `status`: mã trạng thái HTTP như `200`, `301`, `404`, `500`.
- `bytes`: kích thước phản hồi.

### 5.2 Khối Lượng Dữ Liệu

Trong lần chạy thực nghiệm, nhóm đã sinh:

```text
2.000.000 dòng log
```

Dữ liệu được chia trong 3 ngày:

```text
2026-06-01
2026-06-02
2026-06-03
```

Các file log sau khi sinh nằm ở local:

```text
data/raw/2026/06/01/access.log
data/raw/2026/06/02/access.log
data/raw/2026/06/03/access.log
```

## 6. Tổ Chức Dữ Liệu Trên HDFS

Theo yêu cầu đề bài, log được nạp lên HDFS theo cấu trúc thư mục ngày:

```text
/logs/yyyy/MM/dd/access.log
```

Trong lần chạy thực tế:

```text
/logs/2026/06/01/access.log
/logs/2026/06/02/access.log
/logs/2026/06/03/access.log
```

Lợi ích của cách tổ chức này:

- Dễ quản lý log theo ngày.
- Dễ mở rộng khi có log mới.
- Hỗ trợ lọc hoặc xử lý dữ liệu theo khoảng ngày.
- Phù hợp với cách tổ chức dữ liệu lớn trong HDFS.

> **[Ảnh 2 - HDFS UI hiển thị thư mục /logs/2026/06/]**
>
> Gợi ý chụp: mở `http://localhost:9871`, vào phần Browse filesystem và chụp cây thư mục `/logs/2026/06/`.

## 7. Chuẩn Hóa Log Trước Khi Phân Tích

Trước khi chạy các bài toán thống kê, hệ thống chạy một job `normalize` để chuyển log thô thành dạng TSV dễ xử lý.

File xử lý:

```text
streaming/normalize_mapper.py
```

File parser dùng chung:

```text
streaming/apache_log_parser.py
```

Output chuẩn hóa có 7 cột:

```text
day    hour    ip    method    url    status    bytes
```

Ví dụ:

```text
2026-06-01    08    10.10.3.9    GET    /products    200    1234
```

Lý do cần bước chuẩn hóa:

- Các chương trình MapReduce phía sau không phải parse regex nhiều lần.
- Giảm trùng lặp code.
- Dữ liệu trung gian dễ kiểm tra.
- Các mapper/reducer phía sau chỉ cần đọc các cột TSV.

Kết quả normalize được ghi tại:

```text
/bt01/output/normalized
```

Trong lần chạy thực tế, job normalize xử lý đủ:

```text
Map input records  = 2.000.000
Map output records = 2.000.000
```

## 8. Các Chương Trình MapReduce

### 8.1 Chương Trình 1 - Top 20 IP Truy Cập Nhiều Nhất

Files:

```text
streaming/top_ips_global_mapper.py
streaming/top_ips_global_reducer.py
```

Mapper đọc từng dòng dữ liệu đã chuẩn hóa và emit:

```text
ip    1
```

Reducer cộng tổng số request theo từng IP, sau đó giữ lại 20 IP có số lượt truy cập lớn nhất.

Output:

```text
/bt01/output/top_ips_global
```

Kết quả mẫu:

```text
10.10.3.9     1210
10.10.4.60    1206
10.10.1.4     1196
10.10.3.42    1196
10.10.7.50    1182
```

Giải thích khi bảo vệ:

> Mapper biến mỗi lượt truy cập thành một cặp `(IP, 1)`. Hadoop shuffle gom các bản ghi cùng IP về reducer. Reducer cộng số lần xuất hiện của từng IP và sắp xếp để lấy top 20.

### 8.2 Chương Trình Phụ - Đếm IP Theo Ngày Cho Dashboard

Files:

```text
streaming/top_ips_mapper.py
streaming/top_ips_reducer.py
```

Job này không thay thế chương trình top 20 IP toàn cục. Nó được thêm để dashboard có thể lọc top IP theo ngày.

Mapper emit:

```text
day    ip    1
```

Reducer output:

```text
day    ip    hits
```

Kết quả được load vào bảng PostgreSQL `top_ips`.

### 8.3 Chương Trình 2 - Phân Bố Mã HTTP Theo Ngày

Files:

```text
streaming/status_by_day_mapper.py
streaming/status_by_day_reducer.py
```

Mapper emit:

```text
day    status    1
```

Reducer cộng tổng số lần xuất hiện theo cặp `(day, status)`.

Output:

```text
/bt01/output/status_by_day
```

Kết quả mẫu:

```text
2026-06-01    200    333082
2026-06-01    301    66825
2026-06-01    302    66676
2026-06-01    404    133118
2026-06-01    500    66966
```

Giải thích khi bảo vệ:

> Mã `200` biểu thị request thành công, `301/302` là chuyển hướng, `404` là không tìm thấy trang, `500` là lỗi phía server. Việc thống kê theo ngày giúp quan sát chất lượng hệ thống web theo thời gian.

### 8.4 Chương Trình 3 - Top 10 URL Mỗi Ngày

Files:

```text
streaming/top_urls_by_day_mapper.py
streaming/top_urls_by_day_reducer.py
```

Mapper emit:

```text
day    url    1
```

Reducer cộng số lượt truy cập theo từng cặp `(day, url)` và giữ lại top 10 URL cho mỗi ngày.

Output:

```text
/bt01/output/top_urls_by_day
```

Kết quả mẫu:

```text
2026-06-01    /products/laptop    44821
2026-06-01    /cart               44686
2026-06-01    /missing-page       44672
2026-06-01    /assets/app.js      44653
2026-06-01    /products           44538
```

Giải thích khi bảo vệ:

> Job này cho biết trang nào được truy cập nhiều nhất theo từng ngày. Thông tin này hữu ích để phân tích hành vi người dùng hoặc xác định các trang quan trọng cần tối ưu.

### 8.5 Chương Trình 4 - Lưu Lượng Theo 24 Khung Giờ

Files:

```text
streaming/traffic_by_hour_mapper.py
streaming/traffic_by_hour_reducer.py
```

Mapper emit:

```text
day    hour    1
```

Reducer cộng tổng số request theo từng cặp `(day, hour)`.

Output:

```text
/bt01/output/traffic_by_hour
```

Kết quả mẫu:

```text
2026-06-01    00    6934
2026-06-01    01    3510
2026-06-01    02    3472
2026-06-01    03    3548
2026-06-01    04    7091
```

Giải thích khi bảo vệ:

> Job này cho biết website có lượng truy cập cao vào khung giờ nào. Đây là dữ liệu phù hợp để vẽ biểu đồ time series trên dashboard.

## 9. Cấu Hình Hadoop Streaming Và Composite Key

Một số job cần key nhiều cột, ví dụ:

```text
day    status
day    url
day    hour
```

Nếu không cấu hình đúng, Hadoop Streaming có thể chỉ xem cột đầu tiên là key, làm reducer nhận dữ liệu không đúng nhóm.

Vì vậy wrapper:

```text
scripts/hadoop-streaming.sh
```

cấu hình:

```text
stream.num.map.output.key.fields
mapreduce.partition.keypartitioner.options
KeyFieldBasedPartitioner
```

Mục đích:

- Sort/shuffle đúng theo key nhiều cột.
- Đảm bảo reducer nhận dữ liệu theo đúng nhóm.
- Tránh lỗi trùng khóa khi load kết quả vào PostgreSQL.

Ngoài ra, wrapper cũng cấu hình:

```text
PYTHONPATH=.
```

để mapper/reducer có thể import file dùng chung `apache_log_parser.py` khi chạy trên YARN container.

## 10. Theo Dõi Job Bằng YARN

Tất cả job Hadoop Streaming được gửi lên YARN. Có thể theo dõi tại:

```text
http://localhost:8089
```

Các thông tin quan trọng trên YARN UI:

- Application ID
- Tên job
- Trạng thái `RUNNING`, `FINISHED`, `FAILED`
- Thời gian chạy
- Số mapper/reducer
- Log và counters

Trong lần chạy thực tế, các job chính đã hoàn thành thành công:

- `bt01-normalize`
- `bt01-top-20-ips`
- `bt01-ip-counts-by-day`
- `bt01-status-by-day`
- `bt01-top-10-urls-by-day`
- `bt01-traffic-by-hour`

> **[Ảnh 3 - YARN UI hiển thị các job MapReduce hoàn thành]**
>
> Gợi ý chụp: mở `http://localhost:8089`, chụp danh sách application có trạng thái `FINISHED` hoặc màn hình chi tiết một job.

## 11. Kết Quả Đầu Ra

Kết quả MapReduce được ghi trên HDFS:

```text
/bt01/output/normalized
/bt01/output/top_ips_global
/bt01/output/top_ips
/bt01/output/status_by_day
/bt01/output/top_urls_by_day
/bt01/output/traffic_by_hour
```

Sau đó kết quả được export ra thư mục:

```text
dashboard/export/
```

Các file export:

```text
top_ips_global.tsv
top_ips.tsv
status_by_day.tsv
top_urls_by_day.tsv
traffic_by_hour.tsv
```

Số dòng đã load vào PostgreSQL:

```text
top_ips         : 1.301.264 dòng
status_by_day   : 15 dòng
top_urls_by_day : 30 dòng
traffic_by_hour : 72 dòng
```

Giải thích:

- `top_ips` có nhiều dòng vì lưu số lượt truy cập theo từng cặp `(day, ip)`, phục vụ lọc dashboard.
- `status_by_day` có 15 dòng vì có 3 ngày và 5 mã HTTP.
- `top_urls_by_day` có 30 dòng vì có 3 ngày, mỗi ngày lấy top 10 URL.
- `traffic_by_hour` có 72 dòng vì có 3 ngày và 24 giờ mỗi ngày.

## 12. Benchmark 1, 2, 4 Reducer

Script benchmark:

```powershell
.\scripts\04-benchmark-reducers.ps1
```

Benchmark được chạy trên 2 job:

- `status_by_day`
- `traffic_by_hour`

Kết quả thực tế:

| Job | Số reducer | Thời gian |
|---|---:|---:|
| status_by_day | 1 | 26.63s |
| status_by_day | 2 | 27.99s |
| status_by_day | 4 | 28.47s |
| traffic_by_hour | 1 | 28.94s |
| traffic_by_hour | 2 | 27.32s |
| traffic_by_hour | 4 | 28.98s |

Nhận xét:

- Với `status_by_day`, 1 reducer nhanh nhất trong lần đo này.
- Với `traffic_by_hour`, 2 reducer nhanh nhất trong lần đo này.
- 4 reducer không nhanh hơn rõ rệt.

Nguyên nhân:

- Dữ liệu 2 triệu dòng đủ để demo nhưng chưa quá lớn đối với cluster Docker trên một máy cá nhân.
- Các container chia sẻ cùng CPU, RAM và I/O của máy host.
- Tăng reducer làm tăng overhead shuffle, merge và quản lý task.
- Vì vậy thời gian xử lý không giảm tuyến tính khi tăng số reducer.

Kết luận benchmark:

> Việc tăng reducer không phải lúc nào cũng làm chương trình nhanh hơn. Số reducer tối ưu phụ thuộc vào kích thước dữ liệu, số node, tài nguyên cụm và chi phí shuffle.

> **[Ảnh 4 - File benchmark-results.csv hoặc biểu đồ benchmark]**
>
> Gợi ý chụp: mở `docs/benchmark-results.csv`, hoặc vẽ biểu đồ cột so sánh thời gian 1/2/4 reducer rồi chèn vào đây.

## 13. Dashboard Grafana

Sau khi chạy:

```powershell
.\scripts\05-export-results.ps1
.\scripts\06-load-dashboard.ps1
```

dữ liệu được load vào PostgreSQL để Grafana truy vấn.

Truy cập dashboard:

```text
http://localhost:3001
```

Tài khoản:

```text
admin / admin
```

Dashboard `BT01 - Web Log Analysis` gồm:

- Biểu đồ lưu lượng truy cập theo thời gian.
- Bảng/biểu đồ top 20 IP.
- Biểu đồ phân bố mã HTTP theo ngày.
- Bảng top URL mỗi ngày.
- Bộ lọc theo ngày và time picker.

> **[Ảnh 5 - Dashboard Grafana tổng quan]**
>
> Gợi ý chụp: mở dashboard `BT01 - Web Log Analysis`, chọn khoảng thời gian bao gồm `2026-06-01` đến `2026-06-03`, sau đó chụp toàn màn hình dashboard.

> **[Ảnh 6 - Bộ lọc thời gian hoặc lọc ngày trên Grafana]**
>
> Gợi ý chụp: chọn một ngày cụ thể trên biến `day` hoặc time picker để chứng minh dashboard có tính tương tác.

## 14. Các Script Chính Và Chức Năng

| Script | Chức năng |
|---|---|
| `00-start-cluster.ps1` | Khởi động Hadoop/YARN/PostgreSQL/Grafana |
| `01-generate-logs.ps1` | Sinh dữ liệu log |
| `02-load-logs-to-hdfs.ps1` | Nạp log vào HDFS theo `/logs/yyyy/MM/dd/` |
| `03-run-all-jobs.ps1` | Chạy toàn bộ pipeline MapReduce |
| `04-benchmark-reducers.ps1` | Benchmark 1, 2, 4 reducer |
| `05-export-results.ps1` | Export kết quả từ HDFS ra TSV |
| `06-load-dashboard.ps1` | Load TSV vào PostgreSQL |
| `99-stop-cluster.ps1` | Dừng hệ thống |

## 15. Những Lỗi Gặp Phải Và Cách Xử Lý

Trong quá trình triển khai, nhóm gặp một số vấn đề kỹ thuật:

### 15.1 ResourceManager không khởi động

Nguyên nhân:

```text
Queue configuration missing child queue names for root
```

Cách xử lý:

- Bổ sung file `capacity-scheduler.xml`.
- Khai báo queue mặc định `root.default`.

### 15.2 Hadoop Streaming không đọc được thư mục log lồng nhiều cấp

Nguyên nhân:

- Input `/logs` chứa nhiều thư mục con như `/logs/2026/06/01/`.
- Hadoop mặc định không đọc đệ quy toàn bộ thư mục con.

Cách xử lý:

```text
mapreduce.input.fileinputformat.input.dir.recursive=true
```

### 15.3 Mapper không import được file parser dùng chung

Nguyên nhân:

```text
ModuleNotFoundError: No module named 'apache_log_parser'
```

Cách xử lý:

```text
PYTHONPATH=.
```

### 15.4 PowerShell truyền Bash script nhiều dòng bị lỗi quote

Nguyên nhân:

- PowerShell và Bash xử lý quote khác nhau.

Cách xử lý:

- Tách phần Bash nạp log thành file riêng `load-logs-to-hdfs.sh`.
- PowerShell chỉ gọi script Bash trong container.

## 16. Hạn Chế

- Dữ liệu hiện tại là log giả lập, chưa phải log thật từ hệ thống web production.
- Dashboard không đọc trực tiếp từ HDFS mà thông qua PostgreSQL.
- Benchmark chạy trên Docker trong một máy cá nhân nên chưa phản ánh đầy đủ hiệu năng cụm Hadoop thật.
- Các job top-N toàn cục nên chạy 1 reducer để đảm bảo kết quả top chính xác.

## 17. Hướng Mở Rộng

Có thể mở rộng hệ thống theo các hướng:

- Thay dữ liệu giả lập bằng NASA HTTP Log 1995.
- Bổ sung Hive external table để truy vấn kết quả bằng SQL.
- Thêm cơ chế nạp log định kỳ để mô phỏng gần thời gian thực.
- Tối ưu MapReduce bằng combiner hoặc nhiều pha xử lý top-N.
- Bổ sung thêm dashboard về lỗi 404/500 theo URL.
- So sánh hiệu năng giữa Hadoop MapReduce và Spark.

## 18. Kết Luận

Đề tài đã xây dựng được một hệ thống xử lý log web quy mô lớn theo đúng yêu cầu chính của BT01. Hệ thống sử dụng HDFS để lưu trữ dữ liệu phân tán, MapReduce chạy trên YARN để xử lý song song, Python Streaming để triển khai mapper/reducer, và Grafana để trực quan hóa kết quả.

Kết quả thực nghiệm với 2.000.000 dòng log cho thấy hệ thống có thể:

- Tổ chức log theo ngày trên HDFS.
- Chạy các job MapReduce để phân tích IP, mã HTTP, URL và lưu lượng theo giờ.
- Theo dõi job qua YARN Web UI.
- Benchmark với 1, 2, 4 reducer.
- Xuất kết quả sang PostgreSQL và hiển thị trên dashboard tương tác.

Qua quá trình triển khai, nhóm hiểu rõ hơn cách Hadoop xử lý dữ liệu lớn theo mô hình phân tán, vai trò của mapper/reducer, quá trình shuffle/sort, cũng như ảnh hưởng của số reducer đến thời gian xử lý.

## 19. Phụ Lục - Lệnh Chạy Demo

```powershell
cd "D:\Bai tập thứ 6\apache\bt01-web-log-analysis"

.\scripts\00-start-cluster.ps1
.\scripts\01-generate-logs.ps1 -Lines 2000000 -Days 3 -StartDate "2026-06-01"
.\scripts\02-load-logs-to-hdfs.ps1
.\scripts\03-run-all-jobs.ps1
.\scripts\04-benchmark-reducers.ps1
.\scripts\05-export-results.ps1
.\scripts\06-load-dashboard.ps1
```

Các URL demo:

```text
HDFS UI            : http://localhost:9871
YARN UI            : http://localhost:8089
MapReduce History  : http://localhost:19889
Grafana Dashboard  : http://localhost:3001
```

## 20. Phụ Lục - Danh Sách Ảnh Cần Chèn

Bạn nên chèn các ảnh sau vào báo cáo:

| Mã ảnh | Nội dung | Vị trí gợi ý |
|---|---|---|
| Ảnh 1 | Sơ đồ kiến trúc hệ thống | Mục 3 |
| Ảnh 2 | HDFS UI hiển thị `/logs/2026/06/` | Mục 6 |
| Ảnh 3 | YARN UI hiển thị job hoàn thành | Mục 10 |
| Ảnh 4 | Benchmark 1/2/4 reducer hoặc biểu đồ benchmark | Mục 12 |
| Ảnh 5 | Grafana dashboard tổng quan | Mục 13 |
| Ảnh 6 | Grafana lọc theo ngày/khoảng thời gian | Mục 13 |
