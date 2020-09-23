# encoding: utf-8
"""
@version: 1.0
@author: Jarrett
@file: test
@time: 2020/6/3 13:13
"""

import pandas as pd


def ReadDBCFile(dbc_path):
    """
    解读DBC文件
    :param dbc_path: str, dbc file path.
    :return: return dbc, data_title which is a column list.
    """
    dbc_file = pd.read_csv(dbc_path)  # 读取标准格式的dbc文件
    dbc_file.columns = ['v1', 'variable_name', 'v3', 'start_bit', 'address', 'v6', 'data_type', 'data_factor']  # 重命名列名称
    dbc_file = dbc_file[['variable_name', 'start_bit', 'address', 'data_type', 'data_factor']]  # 筛选其中的可用列

    all_signal_name = dbc_file['variable_name'].tolist()
    data_title = ['timestamp'] + all_signal_name  # 设计数据的抬头

    # all_signal_name = pd.DataFrame([data_title])
    # all_signal_name.to_csv(result_path, index=False)  # 将名字写入

    grouped_dbc = dbc_file.groupby('address')  # 按照CAN 的地址进行分组，分组的结果需要用x, y in result 进行遍历解析

    dbc_addr_list = []  # 用于存放所有的地址
    dbc_data_list = []  # 存放和地址对应的所有数据
    dbc_data = {}  # 新建一个字典文件，用来存放dbc的数据，数据格式准备为
    group_length = 0
    for dbc_addr, group_data in grouped_dbc:
        # 分别取到dbc中can的地址和每组的数据
        dbc_data['data'] = group_data  # group_data['variable_name'] # 从dataFrame的格式中转换到字典中
        dbc_data['location'] = group_length  # 各个地址分组的位置，之后用于摆放计算得到的数据
        dbc_data_list.append(dbc_data)
        dbc_data = {}  # 清空该字典
        group_length += group_data.shape[0]  # 返回每个dataframe的列数
        dbc_addr_list.append(dbc_addr)  # 存放分组的地址

    return dbc_addr_list, dbc_data_list, data_title
