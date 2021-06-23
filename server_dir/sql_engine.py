import sqlalchemy
from entity.entity_class import UnameUuid,Users
import pymysql
from sqlalchemy.orm import sessionmaker
import uuid
from collections.abc import Iterable
import hashlib
from apscheduler.schedulers.blocking import BlockingScheduler
import random
import yaml
import os
from sqlalchemy.exc import OperationalError
import time
from server_dir.util import LOGGER
from server_dir.util import CONF

pymysql.install_as_MySQLdb()

conf=CONF
username=conf['database']['username']
password=conf['database']['password']
host=conf['database']['host']
cluster_port=conf['database']['cluster_port']
schema=conf['database']['schema']

#对指定分片的数据进行加密
def encode_pass(pass3,shift_rand,slice,total_slice):
    blake_shift_rand = hashlib.blake2b((str(shift_rand)).encode('utf-8')).hexdigest() #计算shift_rand 的blake2b值,用于分片
    LOGGER.debug("blake_shift_rand:{}".format(blake_shift_rand))
    # 【2.5】计算最后存储在分布式中的密码
    final_pass = cal_final_pass(pass3, blake_shift_rand, total_slice, slice)
    LOGGER.debug("fianl_pass:{}".format(final_pass))
    return final_pass

#计算user表中未经过分布式遍历的固定密码
def cal_user_fix_encode_password(user_password,version,shift_rand,curr_uuid):
    # 【2.2】对密码第一次加密，盐+password md5加密
    pass1 = hashlib.md5((curr_uuid + user_password).encode('utf-8')).hexdigest()  # 首先进行盐+password md5加密
    LOGGER.debug("pass1:{}".format(pass1))
    # 【2.3】 对密码第二次加密，此次加密为将字符串pass1右移,再拼接上盐值(version)，再sha256加密
    pass2 = hashlib.sha256(
        (shift_right_str(pass1, version) + str(version)).encode('utf-8')).hexdigest()  # 首先进行盐+password md5加密
    LOGGER.debug("pass2:{}".format(pass2))
    # 【2.4】 对密码第三次加密，此次加密为对shift_rand(盐值)+pass2  blake2b 加密（最后成了128长度的字符串）,再整体移位shift_rand%128 位
    pass3 = shift_right_str(hashlib.blake2b((str(shift_rand) + pass2).encode('utf-8')).hexdigest(), shift_rand)
    LOGGER.debug("pass3:{}".format(pass3))
    return pass3

#添加一名新用户
def add_user(user_name:str,user_password:str):
    if(len(query_uname_uuid(user_name))>0):
        LOGGER.info("数据库已经存在该用户名,请换一个新的用户名")
        return False
    #得到原始user_name进行2次md5加密后的结果，也即uname_uuid这张表的user_name
    str2 = encode_unameuuid_username(user_name)

    #【1.2】此处的uuid作为salt
    curr_uuid=str(uuid.uuid1())
    #【1.3】构造第一个表的数据，用来记录用户名（进行过2次md5加密），第一张建表完成
    for session in sessions:
        curr_uname_uuid = UnameUuid(user_name=str2, uuid=curr_uuid)
        add_entity(session,curr_uname_uuid)
    LOGGER.debug("user_name:{},两次md5加密存储字符串为:{},uuid:{}".format(user_name,str2,curr_uuid))

    #【2.1】接下来存储第二张表格数据,此处的curr_uuid就相当于是盐值, 并对组合的字符串进行blake2b 哈希加密
    user_name_blake = hashlib.sha256((curr_uuid+str2).encode('utf-8')).hexdigest() #计算加完盐的user_name
    LOGGER.debug("user_name_blake:{}".format(user_name_blake))

    #【2.2】得到或者生成user表必须的shift_rand,version,slice,total_slice等数值，加密的pass需要另外计算
    shift_rand = random.randint(0, 0x7fffffff) #在0到2 147 483 647间产生一个随机数
    version=conf['app']['version']
    slices=[i for i in range(1, len(engines)+1)]
    total_slice=len(engines)

    pass3=cal_user_fix_encode_password(user_password,version,shift_rand,curr_uuid)
    final_pass=[encode_pass(pass3,shift_rand,slices[i],total_slice) for i in range(0, len(slices))]
    LOGGER.info("fianl_pass:{}".format(final_pass))
    curr_users=[Users(user_name=user_name_blake,password=final_pass[i],version=version,shift_rand=shift_rand,slice=slices[i]) for i in range(0,len(final_pass))]
    LOGGER.info("curr_users:{}".format(curr_users))
    for i in range(0,len(sessions)):
        add_entity(sessions[i],curr_users[i])
    return True

#将字符串右移动n位
def shift_right_str(s:str,n:int):
    str_len=len(s)
    n=n%str_len
    s1 = s[0:str_len - n]
    s2 = s[str_len-n:str_len]
    return s2 + s1

#ORM映射，在表中增加元素
def add_entity(session,entity):
    if(isinstance(entity,Iterable)):
        session.add_all(entity)
    else:
        session.add(entity)
    session.commit()

#第一张表的用户名进行两次md5加密
def encode_unameuuid_username(user_name:str):
    #用md5加密两次
    md5_obj = hashlib.md5(user_name.encode("utf-8"))
    str1 = md5_obj.hexdigest()  # 加密1次
    obj2 = hashlib.md5(str1.encode("utf-8"))
    str2 = obj2.hexdigest()  # 加密2次
    return str2

#返回结果列表，如果没有查询到结果则返回空列表
def query_uname_uuid(user_name:str):
    return sessions[0].query(UnameUuid).filter_by(user_name=encode_unameuuid_username(user_name)).all()

#根据user_name获取user表中的一条数据
def query_user(user_name:str):
    temp_uname_uuid=query_uname_uuid(user_name)
    if(len(temp_uname_uuid)<1):
        LOGGER.debug("用户名{}不存在".format(user_name))
        return None,None
    temp_uname_uuid=temp_uname_uuid[0]
    user_name_blake = hashlib.sha256((temp_uname_uuid.uuid + temp_uname_uuid.user_name).encode('utf-8')).hexdigest()
    res=[sessions[i].query(Users).filter_by(user_name=user_name_blake).all()[0] for i in range(0, len(sessions))]
    return temp_uname_uuid,res

# 改变version
def version_auto_inc_job():
    conf['app']['version']=int(conf['app']['version'])+1
    LOGGER.info("当前version已经改变为:{}".format(conf['app']['version']))
    with open('../config.yaml', mode='w', encoding='utf-8') as file: yaml.dump(conf, file)

#定时器定时执行任务，模拟软件迭代的版本，由此将版本号当做盐值融入其中
def time_schedule():
    # BlockingScheduler
    scheduler = BlockingScheduler()
    scheduler.add_job(version_auto_inc_job, 'interval', seconds=5)
    scheduler.start()

#对hexdigest进行分布式混合处理，如hexdigest="12345678",salt="abcdefgh",total_slice=4,curr_slice=2
#则最终的结果为 'ab34efgh'
def cal_final_pass(hexdigest,salt,total_slice,curr_slice):
    if(len(salt)!=len(hexdigest)):
        LOGGER.error("ERROR!!!，salt的长度和hexdigest不一致")
        return None
    if(curr_slice<=0 or curr_slice>total_slice):
        LOGGER.error("ERROR!!! , curr_slice:{} 超出最大界限[1.{}]".format(curr_slice,total_slice))
        return None
    if(total_slice==1):
        return hexdigest
    block_size=len(hexdigest)//total_slice
    if(curr_slice!=total_slice):
        res=hexdigest[(curr_slice-1)*block_size:curr_slice*block_size]
        if(curr_slice==1):
            temp1=""
            temp2=salt[curr_slice*block_size:]
        else:
            temp1=salt[0:(curr_slice-1)*block_size]
            temp2=salt[curr_slice*block_size:]
        final=temp1+res+temp2
    else:
        last_block=len(hexdigest)-(total_slice-1)*block_size
        res=hexdigest[-last_block:]
        temp1=salt[:len(hexdigest)-last_block]
        final=temp1+res
    return final

#测试代码，添加一名新用户
def test_create_user():
    check_mysql_container()
    isOk=add_user("abc1234","wuyi221013")
    if(isOk):
        LOGGER.info("添加用户成功")
    else:
        LOGGER.info("添加用户失败！！！")

#通过命令行来启动docker mysql container
def build_docker_container():
    # create main container cmd
    cluster_port= conf['database']['cluster_port']
    cluster_backup_port=conf['database']['cluster_backup_port']

    # for i in range(cluster_port[0], cluster_port[len(cluster_port)-1] + 1):
    #     cmd="docker run -d -p {}:3306 -v /Users/wuyi/docker/mysql/data{}:/var/lib/mysql --name docker_mysql{} -e MYSQL_ROOT_PASSWORD=wuyi221013 mysql".format(i,i-cluster_port[0]+1,i-cluster_port[0]+1)
    #     print(cmd)
    #     res = os.popen(cmd).read()
    #     print(res)
    for i in range(cluster_backup_port[0],cluster_backup_port[len(cluster_backup_port)-1]+1):
        cmd = "docker run -d -p {}:3306 -v /Users/wuyi/docker/mysql/data{}_backup:/var/lib/mysql --name docker_mysql{}_backup -e MYSQL_ROOT_PASSWORD=wuyi221013 mysql:8.0".format(
            i, i - cluster_backup_port[0]+1, i - cluster_backup_port[0]+1)
        LOGGER.info("cmd:{}".format(cmd))
        res = os.popen(cmd).read()

#检查用户名密码是否存在,返回两个参数，第一个代表账号是否存在，第二个是账号密码是否都存在
def check_username_password(user_name:str,user_password:str):
    temp_uname_uuid,cluster_users=query_user(user_name)
    if(cluster_users is None):
        return False,False
    temp_uuid=temp_uname_uuid.uuid
    temp_version = cluster_users[0].version
    temp_shift_rand = cluster_users[0].shift_rand

    pass3 = cal_user_fix_encode_password(user_password,temp_version,temp_shift_rand,temp_uuid)

    slices = [i for i in range(1, len(engines) + 1)]
    final_pass=[encode_pass(pass3,temp_shift_rand,slices[i], total_slice=len(engines)) for i in range(0, len(slices))]

    #TODO: 蜜罐技术，诱导黑客攻击，此块暂时没写完
    fake_black2_pass = hashlib.blake2b((str(user_password)).encode('utf-8')).hexdigest()
    if fake_black2_pass in final_pass:
        LOGGER.WARNING("警告！当前密码为第一次blake2b加密后的密码，疑似出现黑客攻击！！！")


    for i in range(0, len(slices)):
        if(cluster_users[i].password!=final_pass[i]):
            return True,False;
    return True,True

#测试用户名密码是否存在
def test_user_password_exit():
    # add_user("wuyi111","wuyi221013")
    isOk=check_username_password("wuyi111","wuyi221013")

    if(not isOk[0]):
        print("用户名不存在")
    elif isOk[1]:
        print("用户名密码校验成功，通过")
    else:
        print("密码错误")

#检查docker mysql container 的连接状态，如果当前container发生宕机，立马启动新的container
def check_mysql_container():
    for i in range(0, len(engines)):
        try:
            engines[i].connect()
        except OperationalError as e:
            LOGGER.warning("端口{}连接异常，Error信息如下:{}".format(cluster_port[i],e))
            LOGGER.info("当前端口{}发生故障，正在重新启动docker container".format(cluster_port[i]))
            cmd = "docker ps -a -q --filter \"name=docker_mysql{}\"".format(i + 1)
            broken_container_id = os.popen(cmd).read()
            if(broken_container_id.strip()):
                LOGGER.info("broken_container_id:{}".format(broken_container_id))
                cmd = "docker rm {}".format(broken_container_id)
                os.popen(cmd)  # 删除坏掉的container
                time.sleep(2)

            # 重新建立数据映射并启动新的container
            cmd = "docker run -d -p {}:3306 -v /Users/wuyi/docker/mysql/data{}:/var/lib/mysql --name docker_mysql{} -e MYSQL_ROOT_PASSWORD=wuyi221013 mysql".format(
                cluster_port[i], cluster_port[i] - cluster_port[0] + 1, cluster_port[i] - cluster_port[0] + 1)
            LOGGER.info("cmd:{}".format(cmd))
            res = os.popen(cmd).read()

#创建数据库引擎(连接数据库) echo=True表示显示面向对象的语言转为sql语句
# engine=sqlalchemy.create_engine("mysql://{}:{}@{}:{}/{}".format(username,password,host,port,schema),
#                               encoding='utf8',echo=True) #用户名、密码、主机名、数据库名

engines=[sqlalchemy.create_engine("mysql://{}:{}@{}:{}/{}".format(username,password,host,port,schema),
                              encoding='utf8',echo=True) for port in cluster_port]
#缓存
session_classes = [sessionmaker(bind=engines[i]) for i in range(0, len(engines))]  ##创建与数据库的会话，class,不是实例
sessions = [session_classes[i]() for i in range(0,len(engines))]  # 生成session实例

#检查集群节点状态，若节点宕机，则会自动重启节点服务
check_mysql_container()

if __name__ == '__main__':
    user_exit,pass_right=check_username_password("abc1234","312")
    if user_exit and pass_right:
        print("用户名密码校验通过，登录成功")
    else:
        print("登录失败")
