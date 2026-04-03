from pyspark.sql import SparkSession


spark = (
    SparkSession.builder
    .appName("verify-spark-cluster")
    .master("spark://master:7077")
    .getOrCreate()
)

rows = spark.range(5).collect()
print("ROW_COUNT=", len(rows))
print("LAST_ID=", rows[-1]["id"])

spark.stop()
