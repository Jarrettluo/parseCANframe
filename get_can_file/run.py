# encoding: utf-8
"""
@version: 1.0
@author: 
@file: run.py
@time: 2020/3/30 9:58
"""
import csv
import re
import os
from get_can_file.read_dbc import ReadDBCFile
import pandas as pd
import numpy as np
import time
from multiprocessing import Pool

# 读取CAN数据源文件
class GetFile:
    def __init__(self):
        self.flag = '1'  # 是否删除的flag
        pass

    def open_file(self, filename, flag):
        with open(filename) as f:
            reader = csv.reader(f)
            can_data = list(reader)  # 存储csv文件的数据
        if flag == '1':
            del can_data[0]  # 剔除第一帧CAN抬头
        else:
            pass
        return can_data

# 数据解析
class DataParse:
    def __init__(self):
        self.num_0x = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
        self.num_0d = ['0000', '0001', '0010', '0011',
                       '0100', '0101', '0110', '0111',
                       '1000', '1001', '1010', '1011',
                       '1100', '1101', '1110', '1111']
        self.all_can_data = []
        self.DBC = []

    def GetCanData(self, can_data):
        for data_frame in can_data:
            time_stamp_list = data_frame[1:6]  # csv 存储的是时间戳
            time_stamp_list = [x.rjust(2,'0') for x in time_stamp_list] # 将时间处理为2位数
            time_stamp = ":".join(time_stamp_list)
            msg_id = data_frame[7]  # 存储的是CAN msg id
            first_byte = data_frame[9:13]
            second_byte = data_frame[13:18]
            first_byte.reverse()
            second_byte.reverse()
            # 翻转后拼接
            can_data_ox_list = first_byte + second_byte
            for i, item in enumerate(can_data_ox_list):
                can_data_ox_list[i] = item.rjust(2, '0')
            can_data = ''.join(can_data_ox_list)
            for i in range(len(self.num_0x)):  # 用于替换十进制为二进制字符串
                can_data = re.sub(self.num_0x[i], self.num_0d[i], can_data)
            self.all_can_data.append([time_stamp, msg_id, can_data])
        # 将CAN数据转化为data frame
        can_data_frame = pd.DataFrame(self.all_can_data)
        # 相同id，只保留一秒内第一个数据，其他去掉
        can_data_frame.drop_duplicates(subset=[0, 1], inplace=True)
        # 再将data frame转化为list
        train_data = np.array(can_data_frame)
        train_data_list = train_data.tolist()
        return train_data_list

    # 该解读DBC的模块已废弃
    def GetCanDBCData(self, can_data):
        for item in can_data:
            variable_name = item[1]  # 获取变量名，‘BE010’

            signal_addr = item[2]  # 获取变量地址
            byte_serial = re.findall(r'Data\[((?:.|\n)*?)\]', signal_addr)
            start_bit = signal_addr.split('.')[-1]  # 找到bytes位的地址
            msg_start_bit = (int(byte_serial[0]) * 32) + int(start_bit)

            id_addr = item[3]
            id = id_addr.split(':')[-1]

            variable_type = item[4]
            if variable_type == 'BOOL':
                variable_type = 1
            else:
                variable_type = 1
                pass  # TODO 这里用来定义其他变量类型

            self.DBC.append([id, variable_name, msg_start_bit, variable_type])
        return self.DBC

# CAN数据解析
class CANParse:
    def __init__(self):
        self.CAN_file_name = r'..\init\can_data.csv'
        self.CAN_DBC_file_name = r".\dbc_file\init\can_dbc.csv"  # 打开相对路径

    def can_data_parse(self):
        csvfile = GetFile()
        can_data = csvfile.open_file(self.CAN_file_name, '1')
        can_dbc_data = csvfile.open_file(self.CAN_DBC_file_name, '1')

        data_parse = DataParse()
        can_frame = data_parse.GetCanData(can_data)
        dbc_frame = data_parse.GetCanDBCData(can_dbc_data)
        msg_name = ['TimeStamp', 'ID']
        msg = []
        msg_frame = []
        for frame in can_frame:
            # print(frame)
            for dbc_msg in dbc_frame:
                # print(dbc_msg)
                if dbc_msg[0] == frame[1]:
                    msg_frame_name = dbc_msg[1]  # 获取signal的名字
                    if msg_frame_name in msg_name:
                        len_of_msg_name = len(msg_name) - 2  # 获取已经存在的name列表长度
                    else:
                        # 如果存放名字的列表为初始化的列表，那么写入
                        msg_name.append(msg_frame_name)  # TODO 判断名字是否已经出现在列表中，
                    msg_frame.append((frame[2])[(dbc_msg[2]):(dbc_msg[2] + dbc_msg[3])])
                else:
                    msg_frame.append(frame[2])
            time_stamp = frame[0]
            msg_id = frame[1]
            msg_frame.insert(0, msg_id)  # 在初始位置插入时间戳和id
            msg_frame.insert(0, time_stamp)
            msg.append(msg_frame)
            msg_frame = []

        msg.insert(0, msg_name)
        return msg

# 运算入口
def func(can_data_path, dbc_path, result_path):
    can_data = GetFile().open_file(can_data_path, '1') # 得到CAN数据的dataframe结构
    data_parse = DataParse()    # 初始化类
    can_frame = data_parse.GetCanData(can_data)

    dbc_addr_list, dbc_data_list, data_title = ReadDBCFile(dbc_path)

    len_can_frame = len(can_frame)

    if len_can_frame < 100_000:
        can_frame_list = [can_frame[0: len_can_frame]]
    elif len_can_frame < 300_000:
        can_frame_list = [can_frame[0: 100_000], can_frame[100_000: len_can_frame]]
    elif len_can_frame < 600_000:
        can_frame_list = [can_frame[0: 100_000], can_frame[100_000: 300_000], can_frame[300_000:len_can_frame]]
    elif len_can_frame < 1_000_000:
        can_frame_list = [can_frame[0: 100_000], can_frame[100_000: 300_000], can_frame[300_000:600_000],
                          can_frame[600_000: len_can_frame]]
    elif len_can_frame < 1_500_000:
        can_frame_list = [can_frame[0: 100_000], can_frame[100_000: 300_000], can_frame[300_000:600_000],
                          can_frame[600_000: 1_000_000], can_frame[1_000_000: len_can_frame]]
    else:
        can_frame_list = [can_frame[0: 200_000], can_frame[200_000: 500_000], can_frame[500_000:900_000],
                          can_frame[900_000: len_can_frame]]

    xx = [dbc_addr_list for _ in range(len(can_frame_list))]  # 占位列表，用于空缺一定位置
    yy = [dbc_data_list for _ in range(len(can_frame_list))]  # 占位列表，用于空缺一定位置
    zz = [result_path for _ in range(len(can_frame_list))]  # 占位列表，用于空缺一定位置

    # region 开启多线程区域
    args = list(zip(can_frame_list, xx, yy, zz))
    pool = Pool()
    q = pool.starmap(multiprocess_work, args)
    pool.close()
    pool.join()
    # endregion

    result_df_list = [pd.DataFrame(e) for e in q]  # 对返回值的每一个元素进行操作
    result_data = pd.concat(result_df_list, ignore_index=True)
    result_data.columns = data_title    # 重命名其columns
    data_final = result_data.groupby(result_data['timestamp']).sum() # 将所有数据压缩在一起
    data_final.to_csv(result_path, index=True)  # 写入所有数据

    return True

# 多进程函数
def multiprocess_work(can_frame, dbc_addr_list, dbc_data_list, result_path):
    source_data_result = []
    for frame_index, frame in enumerate(can_frame):
        mmm = ''  # 初始化数据解析结果变量
        frame_addr = '0x' + str(frame[1]).upper()
        source_data = frame[2]
        addr_index = dbc_addr_list.index(frame_addr)  # 通过数据的地址取索引号，这里体现出字典的优势，一行检索！
        dbc_data = dbc_data_list[addr_index]['data']  # 获取该地址的数据
        frame_data = []  # 存放每帧的数据值
        # frame_data.append(frame[0])     # 添加时间戳【可选】
        for row in dbc_data.itertuples():
            # itertuples将DataFrame迭代为元祖
            if row[4] == 'BOOL':
                mmm = int(source_data[row[2]])  # 如果是bool量则切片
            elif row[4] == 'REAL' or row[4] == 'DINT' and row[5] and str(row[2]):
                mmm = source_data[row[2]: (row[2] + 16)]  # 如果是Real和Dint则加长度的切片
                mmm = int(mmm, 2)  # 将二进制数转换为十进制
                mmm = mmm * (row[5])  # 取系数值
            elif row[4] == 'Reserved':
                mmm = None
            frame_data.append(mmm)
        # 布尔值一般list长度大于5，其他值一般小于等于4，过滤
        if len(frame_data) > 5:
            # 对于布尔量，拆分两段后拼接，得到用户想读的数据
            bool_first_byte = frame_data[0:32]
            bool_second_byte = frame_data[32:64]
            bool_first_byte.reverse()
            bool_second_byte.reverse()
            frame_data = bool_first_byte + bool_second_byte
        length = dbc_data_list[addr_index]['location'] # 从dbc数据种取该信号的location信息
        occupied_list = [None for _ in range(length)]  # 占位列表，用于空缺一定位置
        frame_data = [frame[0]] + occupied_list + frame_data  # 必须占位列表在前，有值列表在后
        source_data_result.append(frame_data)

    return source_data_result


if __name__ == '__main__':
    t0 = time.time()
    can_data_path = 'CESHI.csv'
    dbc_path = r'..\dbc_file\init\DBC_std_v1.0.csv'
    result_path = r'C:/Users/jiarui.luo.HIRAIN/PycharmProjects/parseCANframe/result - 0628.csv'
    func(can_data_path, dbc_path, result_path)
    t1 = time.time()
    print(f'{t1 - t0:.3} 秒')
