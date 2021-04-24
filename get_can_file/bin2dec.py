# encoding: utf-8
"""
@version: 1.0
@author: Jarrett
@file: bin2dec
@time: 2020/5/18 14:24
"""

class Bin2Dec():
    def __init__(self):
        pass

    def bin2dec(self, a):
        a_reverse = self.reverse(a)  # 取反
        a_add_1 = self.add_1(a_reverse)  # 二进制加1
        a_int = -int(a_add_1, 2)
        return a_int

    def bin2dec_auto(self, a):
        if a[0] == '1':  # 如果首位是1，复数转换
            a_output = self.bin2dec(a)
        else:
            a_output = int(a, 2)
        return a_output

    def add_1(self, binary_inpute):  # 二进制编码加1
        _, out = bin(int(binary_inpute, 2) + 1).split("b")
        return out

    def reverse(self, binary_inpute):  # 取反操作
        binary_out = list(binary_inpute)
        for epoch, i in enumerate(binary_out):
            if i == "0":
                binary_out[epoch] = "1"
            else:
                binary_out[epoch] = "0"
        return "".join(binary_out)

if __name__ == '__main__':
    bin2dec = Bin2Dec()
    a_origin = "000000000011010"
    a = bin2dec.bin2dec(a_origin)
    print(a) # -32742 这是将上面的字符串强行转换

    b_rev = bin2dec.reverse(a_origin)
    print(b_rev) # 111111111100101
    b = bin2dec.bin2dec(b_rev)
    print(b)    # -27

    c = bin2dec.bin2dec_auto(a_origin)
    print(c)    # 26

    d = bin2dec.bin2dec_auto(b_rev)
    print(d)    # -27

