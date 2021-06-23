from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String
#创建数据库对象需要继承的基类
Base = declarative_base()
class UnameUuid(Base):
    # 数据库表名称
    __tablename__ = 'uname_uuid'
    __table_args__={
        'schema':'pass_proj'
    }
    # 数据库表属性信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255))
    uuid = Column(String(255))

    def __repr__(self):
        return "user_name:"+self.user_name+",uuid:"+str(self.uuid)  # 返回对象绑定的属性：name、sex、id


class Users(Base):
    # 数据库表名称
    __tablename__ = 'users'
    __table_args__={
        'schema':'pass_proj'
    }
    # 数据库表属性信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255))
    password = Column(String(255))
    version=Column(Integer)
    shift_rand=Column(Integer)
    slice=Column(Integer)

    def __repr__(self):
        return "id:{},user_name:{},password:{},version:{},shift_rand:{},slice:{}".format(self.id,self.user_name,self.password,self.version,self.shift_rand,self.slice)