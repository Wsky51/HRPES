from server_dir.key import pub_key
import socket
from server_dir.server_config import *

# 从证书中心申请本机的ca证书
class Certificate():
    def __init__(self):
        self.ca_sock = socket.socket()
        self.ca_sock.connect((ca_ip, ca_port))
        # stg_send(self.ca_sock, str_encode_utf8("hello ca [from server]"))
    def get_ca(self):
        request = "ca {}".format(pub_key)
        stg_send(self.ca_sock, str_encode_utf8(request))
if __name__ == '__main__':
    ca = Certificate()