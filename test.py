# encoding: utf-8
"""
@version: 1.0
@author: Jarrett
@file: test
@time: 2021/3/18 19:46
"""

import pandas as pd

df = pd.read_csv("map_data.csv")
# print(df)

# df.to_json("map.json")

xx = df.values.tolist()

# print(xx)

with open("map2.json", "w") as f:
    f.write(str(xx))
