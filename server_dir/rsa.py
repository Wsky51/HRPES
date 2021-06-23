import hashlib
import random
from client_dir.util import *

class RSA():
    def __init__(self):
        pass
        # li = eratosthenes(fast_pow(10, 6))
        #
        # idx1 = random.randint(0, len(li) - 1)
        # idx2 = random.randint(0, len(li) - 1)
        # p = li[idx1]
        # q = li[idx2]
        # fai = (p - 1) * (q - 1)
        # idx = random.randint(1000, 10000)
        # e = -1
        # while (True):
        #     if (gcd(idx, fai) == 1):
        #         e = idx
        #         break
        #     idx = idx + 1
        # self.p=p
        # self.q=q
        # self.e=e

    #计算n的位数,以这么多位进行分组
    def cal_n_bit(self,n):
        if(n<8):
            return 8
        b_len=math.ceil(math.log2(n))
        for i in range(b_len,b_len+9):
            if(i%8==0):
                return (i-8)
        return b_len-8 #减8是为了确保不会超过n

    #根据p,q和选取的e产生密钥,p,q必须为两个安全的大素数
    def __gen_key(self):
        # print("p:",p,",q:",q,",e:",e)
        n=self.p*self.q
        fai=(self.p-1)*(self.q-1)
        if self.e<=1 or self.e>=fai:
            print("error e value,please input 1<e<fai")
            return
        if gcd(self.e,fai)!=1:
            print("e and fai should be coprime")
            return
        #求e在fai下的乘法逆元
        d=ext_euclid_inv(self.e,fai) #d满足e*d=1(mod fai)
        return [[self.e,n],[d,n]] #返回，公钥和私钥\

    def get_key(self):
        return self.__gen_key()

    #m为明文数字，pub_key为公钥，注意，加密的m必须
    def encode_m(self,m,pub_key):
        return fast_pow_mod(m,pub_key[0],pub_key[1])

    #c为秘文数字，pri_key为公钥
    def decode_c(self,c,pri_key):
        return fast_pow_mod(c,pri_key[0],pri_key[1])

    def test_inv(self):
        a=15
        mod=23
        res=simple_inv(a,mod)
        print("朴素算法：",res)
        print("费马小定理：",inverse(a,mod))
        res=ext_euclid(a, mod)
        print(res)
        print("扩展欧几里得：",res[0]+mod)

    def test_encode_decode(self):
        key=self.get_key()
        print(key)
        for m in range(100,203):
            miwen=self.encode_m(m, key[0])
            # print("miwen：",miwen)
            minwen=self.decode_c(miwen,key[1])
            # print(minwen==m)
            if(minwen!=m):
                print(m)

    #以len为分组长度进行加密分组,arr_len为分组字符的个数
    def str_to_num(self,str,arr_len):
        res=[]
        for i in range(0,len(str),arr_len):
            num=0
            for ch in str[i:i+arr_len]:
                num=(num<<8)|ord(ch)
            res.append(num)
        return res

    #res为int数组，arr_len为分组字符的个数
    def num_to_str(self,arr,arr_len):
        res=""
        for val in arr:
            tmp=""
            for i in range(arr_len):
                asc_num=val&0xFF
                tmp=chr(asc_num)+tmp
                val=val>>8
            res=res+tmp
        return res

    #用公钥对m明文进行加密
    def encode(self,m,pub_key):
        n=pub_key[1]
        # print("n:",n)
        char_len=self.cal_n_bit(n)//8 #计算分组长度,
        # print("char_len:",char_len)
        arr=self.str_to_num(m,char_len) #计算字符串转化为数组
        return [self.encode_m(i,pub_key) for i in arr]

    def decode(self,c,pri_key):
        return [self.decode_c(i,pri_key)for i in c]

    def decode_to_str(self,c,pri_key):
        data= self.decode(c,pri_key)
        n = pri_key[1]
        char_len = self.cal_n_bit(n) // 8  # char_len计算分组长度，最终char_len为字节数

        return self.num_to_str(data, char_len)

    def test_final(self):
        key=self.get_key()
        print(key)
        text="Cryptography and Network Security;2020214269;wuyi"
        en=self.encode(text,key[0])
        print("加密后为：",en)
        de=self.decode(en,key[1])
        print("解密后为：",de)

        de_txt=self.decode_to_str(en, key[1])

        print(de_txt)


    def digi_signature(self,content,pri_key):
        md5=hashlib.md5()
        md5.update(content.encode('utf-8'))
        #生成信息的摘要
        digest= md5.hexdigest()

        #对摘要进行私钥加密
        return self.encode(digest,pri_key)

    def veri_sign(self,content,arr,pub_key):
        md5=hashlib.md5()
        md5.update(content.encode('utf-8'))
        digest= md5.hexdigest()

        decode_str = self.decode_to_str(arr,pub_key)
        return digest == decode_str


if __name__ == '__main__':
    rsa=RSA()

    key = [[7187, 61467355717], [49535765019, 61467355717]]
    pub_key = key[0]
    pri_key = key[1]

    mess="wuyi hello!"

    signature = rsa.digi_signature(mess, pri_key)
    print("signature",signature)


    # test_encode_decode()