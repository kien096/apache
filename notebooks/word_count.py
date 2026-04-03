from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("WordCount")
    .master("spark://master:7077")
    .config("spark.pyspark.python", "/opt/conda/bin/python")
    .getOrCreate()
)

sc = spark.sparkContext

input_path = "hdfs://master:9000/input/sample.txt"

lines = sc.textFile(input_path)
words = lines.flatMap(lambda line: line.split())
pairs = words.map(lambda word: (word, 1))
counts = pairs.reduceByKey(lambda a, b: a + b)
result = counts.sortBy(lambda item: (-item[1], item[0])).collect()

print("WORD COUNT RESULT")
for word, count in result:
    print(f"{word}\t{count}")

spark.stop()
