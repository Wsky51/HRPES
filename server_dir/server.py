import socket

import requests
import json
from server_dir.sql_engine import  *
from server_dir.rsa import RSA
from client_dir.aes import AES

from server_dir.key import pub_key
from server_dir.key import pri_key

from server_dir.server_config import *


class Server():
    def __init__(self):

        self.rsa=RSA()
        self.aes=AES()
        # 创建一个监听的socket
        listen_fd = socket.socket()
        try:
            # 监听端口
            listen_fd.bind(("0.0.0.0", server_port))
            listen_fd.listen(5)
            while True:
                # 等待连接，连接后返回通信用的套接字
                sock_fd, addr = listen_fd.accept()
                print("Received request from {}".format(addr))

                try:
                    # 获取请求方发送的指令
                    # request = str(sock_fd.recv(BUF_SIZE), encoding='utf-8')
                    request = utf8_decode_str(stg_recv(sock_fd))
                    print("request:",request)

                    my_info = "Cryptography and Network Security;2020214269;wuyi"
                    if (request == my_info):  # 进行ssl连接确认
                        self.ssl_con(sock_fd,my_info)
                    else:
                        request = request.split()  # 指令之间使用空白符分割
                        cmd = request[0]  # 指令第一个为指令类型
                        print("cmd:", cmd)

                        if cmd == "url":  # 判断当前需要执行的指令
                            url_add = request[1]  # 得到第二个参数
                            response = self.get_url(url_add)
                        elif cmd == "hello":  # 如果是鉴权消息
                            print("hello recv in server")
                            pass
                        else:
                            response = "Undefined command: " + " ".join(request)
                        stg_send(sock_fd, str_encode_utf8(response))
                        # sock_fd.send(bytes(response, encoding='utf-8'))
                except KeyboardInterrupt:
                    break
                finally:
                    sock_fd.close()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            listen_fd.close()

    def get_url(self, url_add):
        headers = {'Content-type': 'application/json', "charset": "utf-8"}
        response = requests.get(url_add, headers=headers)
        text = response.text
        return text

    def hello(self):
        pass

    def run(self):
        pass

    def get_ca(self):
        data={"ip":server_ip,"port":server_port,"pub_key":pub_key}
        data=json.dumps(data)

        ca_sock = socket.socket()
        ca_sock.connect((ca_ip, ca_port))

        request = "ca"
        #向CA中心发出请求，参数为
        stg_send(ca_sock,str_encode_utf8(request))

        #发送自身的信息
        stg_send(ca_sock,str_encode_utf8(data))

        #获取从ca端返回的证书信息
        certi = utf8_decode_str(stg_recv(ca_sock))
        ca_sock.close()

        #返回证书信息
        return certi

    def ssl_con(self,sock_fd,my_info):
        #先进行一个简短的连接确认
        print("server connection verification information success!")
        stg_send(sock_fd, str_encode_utf8("info status 200"))
        stg_send(sock_fd, str_encode_utf8(my_info))

        hello_msg = utf8_decode_str(stg_recv(sock_fd)) #收到hello消息
        if(hello_msg != "hello"):
            sock_fd.close()
            return
        print("第一阶段：服务器接收到客户端的请求连接，将向客户端发送服务器证书")

        #从CA中心获取证书信息
        ca = self.get_ca()
        #server进行数字签名
        signature = self.rsa.digi_signature(ca, pri_key)
        stg_send(sock_fd, str_encode_utf8(ca))  #向客户端直接发送CA证书
        stg_send(sock_fd, str_encode_utf8(str(signature))) #向客户端发送签名
        print("第二阶段：服务器向客户端发送CA证书完毕")

        client_pubkey=self.rsa_decode(sock_fd,pri_key) #目前还是字符串
        client_pubkey = self.str_to_arr(client_pubkey)
        print("第三阶段：服务器成功获取客户端公钥：",client_pubkey)

        self.rsa_encode(sock_fd,"Confirm client public key",client_pubkey)
        print("         服务器向客户端发送成功获取客户端密钥确认消息，握手完成！")

        encr_algor = self.rsa_decode(sock_fd,pri_key).split(" ")
        self.aes_key=encr_algor[1]
        print("第四阶段：服务器收到客户端协定的对称加密算法为:",encr_algor[0],",密钥为：",encr_algor[1])

        info=encr_algor[0] +" confirm"
        self.rsa_encode(sock_fd,info,client_pubkey)
        print("第五阶段：服务器向客户端发出对称密钥确认信息,完成整个SSL认证过程！")
        self.ssl_try_cmd(sock_fd)

    def ssl_try_cmd(self,sock):
        try:
            # 获取请求方发送的指令
            # request = str(sock_fd.recv(BUF_SIZE), encoding='utf-8')
            request = utf8_decode_str(stg_recv(sock))
            print("request:", request)

            my_info = "Cryptography and Network Security;2020214269;wuyi"
            if (request == my_info):  # 进行ssl连接确认
                self.ssl_con(sock, my_info)
            else:
                request = request  # 指令之间使用空白符分割
                cmd = request.split()[0]  # 指令第一个为指令类型

                if cmd == "url":  # 判断当前需要执行的指令
                    url_add = request[3:]  # 得到第二个参数
                    url_add=self.str_to_arr(url_add)
                    url_add=self.aes.decode_des_to_str(url_add,len(url_add),self.aes_key)
                    print("aes解析要访问的地址为：",url_add)
                    response = str(self.get_url(url_add))
                elif cmd == "hello":  # 如果是鉴权消息
                    print("hello recv in server")
                    pass
                elif cmd=="add":
                    time_schedule() #每隔一段时间进行版本迭代
                    check_mysql_container() #每次添加用户前先进行docker mysql容器状态检查，若出现异常则进行重启
                    print("收到了add消息")# 得到第二个参数
                    add_param = request[3:]  # 得到第二个参数
                    add_param =self.str_to_arr(add_param)
                    add_param = str(self.aes.decode_des_to_str(add_param, len(add_param), self.aes_key)).strip()
                    user_name,password=add_param.split(" ")
                    isOk = add_user(user_name,password)
                    if isOk:
                        response="add user success!"
                    else:
                        response="add user fail!"
                elif cmd == "query":
                    print("收到了query消息")  # 得到第二个参数
                    add_param = request[3:]  # 得到第二个参数
                    add_param = self.str_to_arr(add_param)
                    add_param = str(self.aes.decode_des_to_str(add_param, len(add_param), self.aes_key)).strip()
                    user_name, password = add_param.split(" ")
                    username_exist,password_correct = check_username_password(user_name, password)
                    if not username_exist:
                        response = "username not exist!"
                    elif password_correct:
                        response = "The verification is passed and the login is successful"
                    else:
                        response="Login failed"
                else:
                    response = "Undefined command: " + " ".join(request)

                #进行AES加密后再传输过去
                encode_url_rep = self.aes.aes(response, self.aes_key)
                stg_send(sock, str_encode_utf8(str(encode_url_rep)))
                # sock_fd.send(bytes(response, encoding='utf-8'))
        except KeyboardInterrupt:
            sock.close()
            exit()
        finally:
            sock.close()


    #将诸如"[1,2,3,4]"转化为数组
    def str_to_arr(self,arr):
        arr=arr.strip()
        arr = arr[1:-1].split(',')
        arr = list(map(int, arr))
        return arr


    #RSA发送消息，info为普通的要加密的字符串信息，key为公钥或者私钥
    def rsa_encode(self,socket,info:str,key):
        encode = self.rsa.encode(str(info), key)
        stg_send(socket, str_encode_utf8(str(encode)))

    #RSA解密消息，info为普通的要加密的字符串信息，key为公钥或者私钥，返回字符串
    def rsa_decode(self,socket,key):
        confirm_mess = utf8_decode_str(stg_recv(socket))
        confirm_mess=self.str_to_arr(confirm_mess)
        confirm_mess = self.rsa.decode_to_str(confirm_mess, key)
        new_ca_str=""
        #去除空字符
        for i in confirm_mess:
            if(ord(i)!=0):
                new_ca_str = new_ca_str + i
        return new_ca_str

if __name__ == '__main__':
    server = Server()
