"""
Script chạy bên trong container pyspark-notebook.
Sinh 1 triệu dòng dữ liệu mẫu và chỉ chạy đến phần COUNT toàn bảng
(CSV vs Parquet).
"""
import os
import sys
import time
import shutil

# Flush stdout ngay lập tức
sys.stdout.reconfigure(line_buffering=True)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ============================================================
# 1. SETUP — SparkSession
# ============================================================
print("Khởi tạo SparkSession...", flush=True)
spark = (SparkSession.builder
         .appName("ReadOptimization_1M_CountOnly")
         .master("local[*]")
         .config("spark.sql.shuffle.partitions", "8")
         .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-count")
         .config("spark.driver.memory", "2g")
         .config("spark.ui.enabled", "false")  # Tắt UI để tránh conflict port
         .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")  # Chỉ hiện lỗi, giảm noise
print("=" * 70, flush=True)
print(f"Spark version: {spark.version}", flush=True)
print(f"Master: {spark.sparkContext.master}", flush=True)
print("=" * 70, flush=True)

# ============================================================
# Helper functions
# ============================================================
def timed(name, func):
    t0 = time.time()
    result = func()
    dt = time.time() - t0
    print(f"  [{name}] {dt:.3f}s  →  result = {result}", flush=True)
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
print(f"\n{'='*70}", flush=True)
print(f"SINH DỮ LIỆU: {N_ROWS:,} dòng, 21 cột", flush=True)
print(f"{'='*70}", flush=True)

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

print(f"DataFrame đã tạo (lazy). Tổng số cột: {len(df.columns)}", flush=True)
print("Bắt đầu cache + count...", flush=True)

# Cache để không phải tính lại mỗi lần ghi
df.cache()
row_count = df.count()
print(f"Đã sinh {row_count:,} dòng trong {time.time()-t0:.1f}s", flush=True)
df.printSchema()
df.show(3, truncate=False)

# ============================================================
# 3. GHI RA CSV VÀ PARQUET
# ============================================================
BASE = "/opt/workspace/data/demo-module-4.4-1m"

csv_local       = f"{BASE}/sales_csv"
parquet_local   = f"{BASE}/sales_parquet"
csv_path        = f"file://{csv_local}"
parquet_path    = f"file://{parquet_local}"

# Xoá cũ nếu có
if os.path.exists(BASE):
    shutil.rmtree(BASE, ignore_errors=True)
    time.sleep(1)  # Đợi filesystem sync
os.makedirs(BASE, exist_ok=True)

print(f"\n{'='*70}", flush=True)
print("GHI CSV VÀ PARQUET", flush=True)
print(f"{'='*70}", flush=True)

print("Ghi CSV ...", flush=True)
t0 = time.time()
df.write.mode("overwrite").option("header", "true").csv(csv_path)
t_csv_write = time.time() - t0
print(f"  → CSV ghi xong: {t_csv_write:.1f}s", flush=True)

print("Ghi Parquet ...", flush=True)
t0 = time.time()
df.write.mode("overwrite").parquet(parquet_path)
t_pq_write = time.time() - t0
print(f"  → Parquet ghi xong: {t_pq_write:.1f}s", flush=True)

csv_size = dir_size_mb(csv_local)
pq_size  = dir_size_mb(parquet_local)
print(f"\nDung lượng CSV    : {csv_size:>8.2f} MB", flush=True)
print(f"Dung lượng Parquet: {pq_size:>8.2f} MB", flush=True)
if csv_size > 0:
    print(f"Tỉ lệ nén Parquet/CSV: {pq_size/csv_size*100:.1f}%", flush=True)

# ============================================================
# 4. CSV vs Parquet — ĐO THỜI GIAN COUNT TOÀN BẢNG
# ============================================================
print(f"\n{'='*70}", flush=True)
print("CSV vs PARQUET — COUNT TOÀN BẢNG", flush=True)
print(f"{'='*70}", flush=True)

print("COUNT toàn bảng:", flush=True)
t_csv = timed("CSV    ", lambda: spark.read.option("header", "true").csv(csv_path).count())
t_pq  = timed("Parquet", lambda: spark.read.parquet(parquet_path).count())
if t_pq > 0:
    print(f"\n→ Parquet nhanh hơn CSV {t_csv/t_pq:.1f}x lần", flush=True)

# ============================================================
# DONE — Dừng ở đây theo yêu cầu
# ============================================================
print(f"\n{'='*70}", flush=True)
print("HOÀN TẤT — Chỉ chạy đến phần COUNT toàn bảng", flush=True)
print(f"{'='*70}", flush=True)

# Cleanup
df.unpersist()
spark.stop()
print("\nDone! ✅", flush=True)
