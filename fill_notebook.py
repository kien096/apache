import json
import re

nb_path = r'd:\Bai tập thứ 6\apache\notebooks\03-spark-dataframes.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "load('../data/tweets.json')" in source:
            cell['source'] = [s.replace("../data/tweets.json", "file:///opt/workspace/data/tweets.json") for s in cell['source']]
        if "'../data/shakespeare.txt'" in source:
            cell['source'] = [s.replace("../data/shakespeare.txt", "file:///opt/workspace/data/shakespeare.txt") for s in cell['source']]

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f)
