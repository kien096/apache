#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 5 ]; then
  echo "Usage: hadoop-streaming.sh <job-name> <input> <output> <mapper.py> <reducer.py|NONE> [reducers] [key-fields]" >&2
  exit 2
fi

job_name="$1"
input_path="$2"
output_path="$3"
mapper="$4"
reducer="$5"
reducers="${6:-1}"
key_fields="${7:-1}"

streaming_jar="$(find /opt/hadoop/share/hadoop/tools/lib -name 'hadoop-streaming*.jar' | head -n 1)"
if [ -z "$streaming_jar" ]; then
  echo "Cannot find hadoop-streaming jar" >&2
  exit 1
fi

hdfs dfs -rm -r -f "$output_path" >/dev/null 2>&1 || true

file_args=(
  -file "/opt/bt01/streaming/apache_log_parser.py"
  -file "/opt/bt01/streaming/$mapper"
)
if [ "$reducer" != "NONE" ]; then
  file_args+=(-file "/opt/bt01/streaming/$reducer")
fi

streaming_args=(
  jar "$streaming_jar"
  -D "mapreduce.job.name=$job_name"
  -D "mapreduce.job.reduces=$reducers"
  -D "mapreduce.input.fileinputformat.input.dir.recursive=true"
  -D "stream.num.map.output.key.fields=$key_fields"
  -D "mapreduce.partition.keypartitioner.options=-k1,$key_fields"
  -partitioner org.apache.hadoop.mapred.lib.KeyFieldBasedPartitioner
  "${file_args[@]}"
  -cmdenv "PYTHONPATH=."
  -mapper "python3 $mapper"
  -input "$input_path"
  -output "$output_path"
)

if [ "$reducer" = "NONE" ]; then
  hadoop "${streaming_args[@]}"
else
  hadoop "${streaming_args[@]}" \
    -reducer "python3 $reducer"
fi

if ! hdfs dfs -test -e "$output_path/_SUCCESS"; then
  echo "Streaming job failed or did not create $output_path/_SUCCESS" >&2
  exit 1
fi
