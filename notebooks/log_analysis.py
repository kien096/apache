from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("LogAnalysis")
    .master("spark://master:7077")
    .config("spark.pyspark.python", "/opt/conda/bin/python")
    .config("spark.cores.max", "4")
    .config("spark.executor.cores", "2")
    .getOrCreate()
)

sc = spark.sparkContext

logs = sc.textFile("hdfs://master:9000/input/server.log")

errors = logs.filter(lambda line: "ERROR" in line)
print(f"Tong so loi: {errors.count()}")

error_types = errors.map(lambda line: (line.split()[3], 1))
error_counts = error_types.reduceByKey(lambda a, b: a + b)
result = error_counts.sortBy(lambda item: (-item[1], item[0])).collect()

print("LOG ANALYSIS RESULT")
for error_type, count in result:
    print(f"{error_type}\t{count}")

spark.stop()
