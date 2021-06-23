import socket
from ca_dir.key import *
from ca_dir.config import *
import json
import datetime
from ca_dir.rsa import RSA

#做认证中心使用
class CA():
    def __init__(self):
        # 创建一个监听的socket
        listen_fd = socket.socket()
        try:
            # 监听端口
            listen_fd.bind(("0.0.0.0",ca_port))
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

                    request = request.split()  # 指令之间使用空白符分割
                    cmd = request[0]  # 指令第一个为指令类型

                    if cmd == "ca":  # 判断当前需要执行的指令,
                        self.get_ca(sock_fd)

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
    def get_ca(self,sock_fd):
        j_data = utf8_decode_str(stg_recv(sock_fd))
        meg_data = json.loads(j_data)

        # 获取服务器传来的信息
        server_ip = meg_data['ip']
        server_port = meg_data['port']
        server_pub_key = meg_data['pub_key']

        # 设置到期时间为2022年1月1日
        date = datetime.date(2022, 1, 1)
        date = str(date)

        # 用CA自己的私钥对这些信息用RSA加密
        certi_info = dict()
        certi_info['server_ip'] = server_ip
        certi_info['server_pub_key'] = server_pub_key
        certi_info['vaild_date'] = date
        j_certi_info = json.dumps(certi_info)

        #用CA的私钥对信息进行加密
        rsa=RSA()
        encode = rsa.encode(j_certi_info, pri_key)
        encode=str(encode)

        print("将要发送的ca:",encode)

        #将证书发送给server端
        stg_send(sock_fd, str_encode_utf8(encode))


if __name__ == '__main__':
    ca= CA()
