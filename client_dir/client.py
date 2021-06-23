import datetime
import json
import socket
from optparse import OptionParser

from client_dir.config import *
from client_dir.key import pri_key
from client_dir.key import pub_key
from client_dir.rsa import RSA
from client_dir.aes import AES

class Client:
    def __init__(self):
        self.client_sock = socket.socket()
        self.client_sock.connect((server_ip, server_port))
        self.rsa = RSA()
        self.aes = AES()
        self.auth = False

    # 进行一个简短的验证
    def brief_veri(self):
        # 发送信息进行认证
        my_info = "Cryptography and Network Security;2020214269;wuyi"
        stg_send(self.client_sock, str_encode_utf8(my_info))
        rsp1 = utf8_decode_str(stg_recv(self.client_sock))
        rsp2 = utf8_decode_str(stg_recv(self.client_sock))
        if rsp1.find("200") > -1 and rsp2 == my_info:
            print("client connection verification information success!")
        # request = "hello"
        # stg_send(self.client_sock,str_encode_utf8(request))

    # 验证CA证书的有效性
    def veri_ca(self, ca):
        ca_str = str(self.rsa.decode_to_str(ca, ca_pub_key))
        new_ca_str = ""
        # 去除空字符
        for i in ca_str:
            if (ord(i) != 0):
                new_ca_str = new_ca_str + i
        try:
            json_ca = json.loads(new_ca_str)
            return json_ca
        except ValueError:
            return None

    # 检查CA信息的有效性
    def check_json_ca(self, json_ca, signature, content):
        if (json_ca != None):
            print("         客户端解析CA证书成功，CA证书解码信息如下：", json_ca)

            # 获取json的值
            self.server_ip_ = json_ca['server_ip']
            self.server_pub_key_ = json_ca['server_pub_key']
            self.vaild_date_ = json_ca['vaild_date']

            today = datetime.date.today()
            today = str(today)

            # 验证证书的有效性
            if server_ip != self.server_ip_:
                print("server ip 不一致，证书无效！")
                self.client_sock.close()
                exit()
            if today > self.vaild_date_:
                print("证书有效日期过期【超过当前时间】，证书无效！")
                self.client_sock.close()
                exit()

            # 验证数字签名
            sign = self.rsa.veri_sign(content, signature, self.server_pub_key_)
            if (not sign):
                print("         ERROR!!! 数字签名不正确，无效！")
                self.client_sock.close()
                exit()
            print("         客户端验证CA证书有效性通过，确认连接")

        else:
            print("     CA证书校验不通过，结束本进程")
            self.client_sock.close()
            exit()

    def ssl_connect(self):
        self.brief_veri()  # 首先进行一个简单的通信验证

        print("第一阶段：客户端向服务器发送hello消息")
        ca, signature = self.hello()
        ca = self.str_to_arr(ca)
        signature = self.str_to_arr(signature)

        print("第二阶段：客户端收到服务器的CA证书信息")
        json_ca = self.veri_ca(ca)

        # 验证CA证书有效
        self.check_json_ca(json_ca, signature, str(ca))

        print("第三阶段：客户端向服务器发送自身公钥")
        self.rsa_encode(self.client_sock, str(pub_key), self.server_pub_key_)

        new_ca_str = self.rsa_decode(self.client_sock, pri_key)

        if (new_ca_str == "Confirm client public key"):
            print("第四阶段：客户端收到服务器端确认，客户端公钥传输成功")
        else:
            print("第四阶段：公钥传输失败")
            self.client_sock.close()
            exit()

        print("第五阶段：协商加密算法")
        request = "AES {}".format(aes_key)
        self.rsa_encode(self.client_sock,request,self.server_pub_key_)

        new_ca_str = self.rsa_decode(self.client_sock, pri_key)
        if new_ca_str == "AES confirm":
            print("第六阶段：客户端收到服务器端对称加密算法的确认信息，完成整个SSL认证过程！")
            self.auth = True
        else:
            print("第六阶段：未收到服务器端确认消息")
            self.client_sock.close()
            exit()



    # 客户端第一阶段，向服务器端发送hello消息
    def hello(self):
        request = "hello"

        stg_send(self.client_sock, str_encode_utf8(request))
        ca = utf8_decode_str(stg_recv(self.client_sock))
        signature = utf8_decode_str(stg_recv(self.client_sock))
        return ca, signature

    def request_url(self, url):
        request = "url {}".format(url)
        stg_send(self.client_sock, bytes(request, encoding='utf-8'))
        # self.client_sock.send(bytes(request, encoding='utf-8'))
        response = utf8_decode_str(stg_recv(self.client_sock))

        response=self.str_to_arr(response)
        if(self.auth):
            response=self.aes.decode_des_to_str(response,len(response),aes_key)
        return response


    def send_url(self, url):
        if (self.auth):  # 已经鉴权了
            pass
        else:  # 没有鉴权需要首先进行ssl验证
            my_info = "Cryptography and Network Security;2020214269;wuyi"
            request = "hello {}".format(my_info)
            stg_send(self.client_sock, str_encode_utf8(request))  # 发送 hello 消息进行鉴权

    # 将诸如"[1,2,3,4]"转化为数组
    def str_to_arr(self, arr):
        arr=arr.strip()
        arr = arr[1:-1].split(',')
        arr = list(map(int, arr))
        return arr

    def test(self):
        stg_send(self.client_sock, bytes("nihao", encoding='utf-8'))
        stg_send(self.client_sock, bytes("hellp", encoding='utf-8'))
        stg_send(self.client_sock, bytes("fan", encoding='utf-8'))

    # RSA发送消息，info为普通的要加密的字符串信息，key为公钥或者私钥
    def rsa_encode(self, socket, info: str, key):
        encode = self.rsa.encode(str(info), key)
        stg_send(socket, str_encode_utf8(str(encode)))

    # RSA解密消息，info为普通的要加密的字符串信息，key为公钥或者私钥
    def rsa_decode(self, socket, key):
        confirm_mess = utf8_decode_str(stg_recv(socket))
        confirm_mess = self.str_to_arr(confirm_mess)
        confirm_mess = self.rsa.decode_to_str(confirm_mess, key)
        new_ca_str = ""
        # 去除空字符
        for i in confirm_mess:
            if (ord(i) != 0):
                new_ca_str = new_ca_str + i
        return new_ca_str

    def ssl_surf_internet(self,url:str):
        if not self.auth: #已经成功建立了ssl连接
            # 建立ssl连接
            self.ssl_connect()
        aes_encode_url = self.aes.aes(url, aes_key)
        response = self.request_url(str(aes_encode_url))

        print("经过ssl vpn之后的访问网站的结果为：\n",response)

    #客户端向服务器端注册一名新用户
    def add_user(self,user_name,password):
        if not self.auth: #已经成功建立了ssl连接
            # 建立ssl连接
            self.ssl_connect()
        val=user_name+" "+password
        aes_encode_url = self.aes.aes(val, aes_key)
        request = "add {}".format(aes_encode_url)
        stg_send(self.client_sock, bytes(request, encoding='utf-8'))

        response = utf8_decode_str(stg_recv(self.client_sock))
        response=self.str_to_arr(response)
        if(self.auth):
            response=self.aes.decode_des_to_str(response,len(response),aes_key)
        print("response :",response)

    #客户端向服务器端注册一名新用户
    def check_user(self,user_name,password):
        if not self.auth: #已经成功建立了ssl连接
            # 建立ssl连接
            self.ssl_connect()
        val=user_name+" "+password
        aes_encode_url = self.aes.aes(val, aes_key)
        request = "query {}".format(aes_encode_url)
        stg_send(self.client_sock, bytes(request, encoding='utf-8'))

        response = utf8_decode_str(stg_recv(self.client_sock))
        response=self.str_to_arr(response)
        if(self.auth):
            response=self.aes.decode_des_to_str(response,len(response),aes_key)
        print("response :",response)


if __name__ == '__main__':
    client = Client()
    client.add_user("wuyi123","123456")
    # parser = OptionParser()
    # parser.add_option("-a", "--add", dest="user_info", help="add a new user in database")
    # parser.add_option("-q", "--query", dest="query_info", help="query if there is a user in database")
    # options, args = parser.parse_args()
    #
    # user_info=options.user_info
    # # query_info=options.query_info
    # print("user_info:",user_info)

