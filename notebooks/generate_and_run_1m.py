"""
Script chạy bên trong container pyspark-notebook.
Sinh 1 triệu dòng dữ liệu mẫu và thực hiện toàn bộ các bài test
tối ưu hoá đọc dữ liệu trong Spark (CSV vs Parquet, Predicate Pushdown,
Column Pruning, Partition Pruning, kết hợp cả 3).

Chạy bằng: spark-submit --driver-memory 2g generate_and_run_1m.py
"""
import os
import time
import shutil
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *

# ============================================================
# 1. SETUP — SparkSession
# ============================================================
spark = (SparkSession.builder
         .appName("ReadOptimization_1M")
         .master("local[*]")
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
         .config("spark.driver.memory", "2g")
         .getOrCreate())

spark.sparkContext.setLogLevel("WARN")
print("=" * 70)
print(f"Spark version: {spark.version}")
print(f"Master: {spark.sparkContext.master}")
print("=" * 70)

# ============================================================
# Helper functions
# ============================================================
def timed(name, func):
    t0 = time.time()
    result = func()
    dt = time.time() - t0
    print(f"  [{name}] {dt:.3f}s  →  result = {result}")
    return dt

def dir_size_mb(path):
    """Tính dung lượng thư mục"""
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)

# ============================================================
# 2. SINH DỮ LIỆU MẪU — 1 TRIỆU DÒNG, 21 CỘT
# ============================================================
N_ROWS = 1_000_000
print(f"\n{'='*70}")
print(f"SINH DỮ LIỆU: {N_ROWS:,} dòng, 21 cột")
print(f"{'='*70}")

t0 = time.time()
df = (spark.range(0, N_ROWS)
      .withColumn("year",     (F.col("id") % 3 + 2023).cast("int"))
      .withColumn("month",    (F.col("id") % 12 + 1).cast("int"))
      .withColumn("city",     F.element_at(F.array(
          F.lit("HCM"), F.lit("HN"), F.lit("DN"), F.lit("CT"), F.lit("HP")
      ), (F.col("id") % 5 + 1).cast("int")))
      .withColumn("category", F.concat(F.lit("cat_"), (F.col("id") % 10).cast("string")))
      .withColumn("amount",   (F.rand() * 1000).cast("double"))
      .withColumn("quantity", (F.col("id") % 100).cast("int")))

# Thêm 14 cột số phụ — quan trọng cho demo column pruning
for i in range(14):
    df = df.withColumn(f"extra_col_{i}", (F.rand() * 10000).cast("double"))

# Cache để không phải tính lại mỗi lần ghi
df.cache()
row_count = df.count()
print(f"Đã sinh {row_count:,} dòng trong {time.time()-t0:.1f}s")
print(f"Tổng số cột: {len(df.columns)}")
df.printSchema()
df.show(3, truncate=False)

# ============================================================
# 3. GHI RA CSV VÀ PARQUET — SO SÁNH
# ============================================================
BASE = "/opt/workspace/data/demo-module-4.4-1m"

csv_local       = f"{BASE}/sales_csv"
parquet_local   = f"{BASE}/sales_parquet"
csv_path        = f"file://{csv_local}"
parquet_path    = f"file://{parquet_local}"

# Xoá cũ nếu có
if os.path.exists(BASE):
    shutil.rmtree(BASE)
os.makedirs(BASE, exist_ok=True)

print(f"\n{'='*70}")
print("GHI CSV VÀ PARQUET")
print(f"{'='*70}")

print("Ghi CSV ...")
t0 = time.time()
df.write.mode("overwrite").option("header", "true").csv(csv_path)
t_csv_write = time.time() - t0
print(f"  → CSV ghi xong: {t_csv_write:.1f}s")

print("Ghi Parquet ...")
t0 = time.time()
df.write.mode("overwrite").parquet(parquet_path)
t_pq_write = time.time() - t0
print(f"  → Parquet ghi xong: {t_pq_write:.1f}s")

csv_size = dir_size_mb(csv_local)
pq_size  = dir_size_mb(parquet_local)
print(f"\nDung lượng CSV    : {csv_size:>8.2f} MB")
print(f"Dung lượng Parquet: {pq_size:>8.2f} MB")
if csv_size > 0:
    print(f"Tỉ lệ nén Parquet/CSV: {pq_size/csv_size*100:.1f}%")

# ============================================================
# 4. CSV vs Parquet — TỐC ĐỘ ĐỌC (COUNT)
# ============================================================
print(f"\n{'='*70}")
print("CSV vs PARQUET — COUNT TOÀN BẢNG")
print(f"{'='*70}")
t_csv = timed("CSV    ", lambda: spark.read.option("header", "true").csv(csv_path).count())
t_pq  = timed("Parquet", lambda: spark.read.parquet(parquet_path).count())
if t_pq > 0:
    print(f"\n→ Parquet nhanh hơn CSV {t_csv/t_pq:.1f}x lần")

# ============================================================
# 5. PREDICATE PUSHDOWN
# ============================================================
print(f"\n{'='*70}")
print("PREDICATE PUSHDOWN — FILTER year=2024 AND city='HCM'")
print(f"{'='*70}")

df_pq = spark.read.parquet(parquet_path)
df_csv = spark.read.option("header", "true").csv(csv_path)

# Xem physical plan Parquet
print("\n--- PHYSICAL PLAN (Parquet) — chú ý PushedFilters ---")
filtered_pq = df_pq.filter((F.col("year") == 2024) & (F.col("city") == "HCM"))
filtered_pq.explain(mode="formatted")

# Xem physical plan CSV
print("\n--- PHYSICAL PLAN (CSV) — KHÔNG có PushedFilters thực sự ---")
filtered_csv = df_csv.filter((F.col("year") == 2024) & (F.col("city") == "HCM"))
filtered_csv.explain(mode="formatted")

# Đo thời gian filter
print("\nĐo thời gian FILTER:")
t_csv_f = timed("CSV    ", lambda: df_csv.filter((F.col("year") == 2024) & (F.col("city") == "HCM")).count())
t_pq_f  = timed("Parquet", lambda: df_pq.filter((F.col("year") == 2024) & (F.col("city") == "HCM")).count())
if t_pq_f > 0:
    print(f"\n→ Predicate pushdown giúp Parquet nhanh hơn {t_csv_f/t_pq_f:.1f}x lần")

# ============================================================
# 6. COLUMN PRUNING
# ============================================================
print(f"\n{'='*70}")
print("COLUMN PRUNING — 21 CỘT vs 2 CỘT")
print(f"{'='*70}")

print("\nPARQUET:")
t_all_pq = timed("All 21 cols", lambda: spark.read.parquet(parquet_path).select("*").count())
t_2_pq   = timed("2 cols     ", lambda: spark.read.parquet(parquet_path).select("city", "amount").count())

print("\nCSV:")
t_all_csv = timed("All 21 cols", lambda: spark.read.option("header", "true").csv(csv_path).select("*").count())
t_2_csv   = timed("2 cols     ", lambda: spark.read.option("header", "true").csv(csv_path).select("city", "amount").count())

if t_2_pq > 0:
    print(f"\n→ Parquet: chọn 2 cột nhanh hơn chọn 21 cột {t_all_pq/t_2_pq:.1f}x lần")
if t_2_csv > 0:
    print(f"→ CSV    : chọn 2 cột vs 21 cột {t_all_csv/t_2_csv:.1f}x — không có pruning thực sự")

# Xem plan
print("\n--- ReadSchema chỉ chứa 2 cột (Parquet) ---")
spark.read.parquet(parquet_path).select("city", "amount").explain(mode="formatted")

# ============================================================
# 7. PARTITION PRUNING
# ============================================================
print(f"\n{'='*70}")
print("PARTITION PRUNING — partitionBy(year, month)")
print(f"{'='*70}")

partitioned_local = f"{BASE}/sales_partitioned"
partitioned_path  = f"file://{partitioned_local}"

print("Ghi data với partitionBy(year, month) ...")
t0 = time.time()
df.write.mode("overwrite").partitionBy("year", "month").parquet(partitioned_path)
print(f"  → Ghi xong: {time.time()-t0:.1f}s")

# Xem cấu trúc thư mục
print("\nCấu trúc thư mục partition:")
for root, dirs, files in os.walk(partitioned_local):
    level = root.replace(partitioned_local, '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}{os.path.basename(root)}/")
    if level >= 2:
        break

# So sánh filter
print("\nFILTER year=2024 AND month=6:")
t_no_part = timed("Không partition",
    lambda: spark.read.parquet(parquet_path)
             .filter((F.col("year") == 2024) & (F.col("month") == 6)).count())
t_part = timed("Có partition   ",
    lambda: spark.read.parquet(partitioned_path)
             .filter((F.col("year") == 2024) & (F.col("month") == 6)).count())
if t_part > 0:
    print(f"\n→ Partition pruning nhanh hơn {t_no_part/t_part:.1f}x lần")
    print(f"→ Số partition được đọc: 1/36 = {1/36*100:.1f}% dữ liệu")

# Physical plan
print("\n--- PartitionFilters + PushedFilters ---")
(spark.read.parquet(partitioned_path)
  .filter((F.col("year") == 2024) & (F.col("month") == 6) & (F.col("city") == "HCM"))
  .explain(False))

# ============================================================
# 7b. SMALL FILE PROBLEM
# ============================================================
print(f"\n{'='*70}")
print("SMALL FILE PROBLEM — partition theo cột high-cardinality")
print(f"{'='*70}")

bad_partition_local = f"{BASE}/sales_bad_partition"
bad_partition_path  = f"file://{bad_partition_local}"
print("Ghi với partitionBy(quantity) — 100 giá trị khác nhau...")
df.write.mode("overwrite").partitionBy("quantity").parquet(bad_partition_path)

n_files = sum(len(files) for _, _, files in os.walk(bad_partition_local))
size_mb = dir_size_mb(bad_partition_local)
print(f"\nSố file tạo ra : {n_files}")
print(f"Dung lượng     : {size_mb:.2f} MB")
if n_files > 0:
    print(f"Trung bình/file: {size_mb*1024/n_files:.1f} KB  ← QUÁ NHỎ!")

n_files_good = sum(len(files) for _, _, files in os.walk(partitioned_local))
size_mb_good = dir_size_mb(partitioned_local)
print(f"\nĐể so sánh — partition theo (year, month):")
print(f"Số file        : {n_files_good}")
if n_files_good > 0:
    print(f"Trung bình/file: {size_mb_good*1024/n_files_good:.1f} KB")

# ============================================================
# 8. KẾT HỢP CẢ 3 KỸ THUẬT
# ============================================================
print(f"\n{'='*70}")
print("KẾT HỢP CẢ 3: Tổng doanh thu HCM, tháng 6/2024")
print(f"{'='*70}")

def query_slow():
    return (spark.read.option("header", "true").csv(csv_path)
            .filter((F.col("year") == 2024) & (F.col("month") == 6) & (F.col("city") == "HCM"))
            .agg(F.sum(F.col("amount").cast("double")).alias("total"))
            .collect()[0]["total"])

def query_fast():
    return (spark.read.parquet(partitioned_path)
            .filter((F.col("year") == 2024) & (F.col("month") == 6) & (F.col("city") == "HCM"))
            .select("amount")
            .agg(F.sum("amount").alias("total"))
            .collect()[0]["total"])

t_slow = timed("CSV (không tối ưu)         ", query_slow)
t_fast = timed("Parquet + partition + pruning", query_fast)

if t_fast > 0:
    print(f"\n🚀 Tổng tăng tốc: {t_slow/t_fast:.1f}x lần")

# Physical plan đầy đủ
print("\n--- PHYSICAL PLAN HOÀN CHỈNH (cả 3 kỹ thuật) ---")
(spark.read.parquet(partitioned_path)
  .filter((F.col("year") == 2024) & (F.col("month") == 6) & (F.col("city") == "HCM"))
  .select("amount")
  .agg(F.sum("amount"))
  .explain(True))

# ============================================================
# 9. TỔNG KẾT
# ============================================================
print(f"\n{'='*70}")
print("TỔNG KẾT")
print(f"{'='*70}")
print(f"""
╔══════════════════════════════╦══════════════════════════════════════════╗
║ Kỹ thuật                     ║ Khi nào hiệu quả                        ║
╠══════════════════════════════╬══════════════════════════════════════════╣
║ Format Parquet/ORC           ║ Luôn luôn (trừ khi cần human-readable)   ║
║ Predicate Pushdown           ║ Filter trên cột có index/statistics      ║
║ Column Pruning               ║ Bảng nhiều cột, query chỉ cần vài cột   ║
║ Partition Pruning            ║ Query thường lọc theo cột partition      ║
╚══════════════════════════════╩══════════════════════════════════════════╝

Dữ liệu test: {N_ROWS:,} dòng × {len(df.columns)} cột
CSV size    : {csv_size:.2f} MB
Parquet size: {pq_size:.2f} MB
""")
if csv_size > 0:
    print(f"Nén         : {pq_size/csv_size*100:.1f}%")

# Cleanup
df.unpersist()
spark.stop()
print("\nDone! ✅")
