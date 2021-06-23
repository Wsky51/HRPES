import mysql.connector  # 先安装mysql-connector-python-1.0.12-py3.3,再引入包  pip install mysql-connector


# 创建链接数据库
def connect(opt):
    config = {'host': opt['host'] or '127.0.0.1',  # 默认127.0.0.1
              'user': opt['user'] or 'root',
              'password': opt['password'] or 'wuyi221013',
              'port': opt['port'] or 3306,  # 默认即为3306
              'database': opt['database'] or 'pass_proj',
              'charset': opt['charset'] or 'utf8',  # 默认即为utf8
              'auth_plugin' : 'mysql_native_password'
              }
    print(config)
    try:
        mydb = mysql.connector.connect(**config)  # connect方法加载config的配置进行数据库的连接，完成后用一个变量进行接收
    except mysql.connector.Error as e:
        print('数据库链接失败！', str(e))
    else:  # try没有异常的时候才会执行
        print("数据库连接sucessfully!")
        return mydb

    # 插入
    # sql = "INSERT INTO sites (name, url) VALUES (%s, %s)"
    # val = ("RUNOOB", "https://www.runoob.com")


def add(mydb, sql, val):
    mycursor = mydb.cursor()
    mycursor.execute(sql, val)
    mydb.commit()  # 数据表内容有更新，必须使用到该语句
    print(mycursor.rowcount, "记录插入成功。")

    # 更新
    # sql = "UPDATE sites SET name = %s WHERE name = %s"
    # val = ("Zhihu", "ZH")


def update(mydb, sql, val):
    mycursor = mydb.cursor()
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, " 条记录被修改")

    # 查询
    # sql="SELECT * FROM sites"


def query(mydb, sql):
    mycursor = mydb.cursor()
    mycursor.execute(sql)
    myresult = mycursor.fetchall()  # fetchall() 获取所有记录
    for x in myresult:
        print(x)
    return myresult

    # 删除
    # sql = "DELETE FROM sites WHERE name = 'stackoverflow'"
def delete(mydb, sql):
    mycursor = mydb.cursor()
    mycursor.execute(sql)
    mydb.commit()
    print(mycursor.rowcount, " 条记录删除")

if __name__ == '__main__':
    opt={'host':"localhost",'user':"root",'password':"wuyi221013",'port':3306,'database':"pass_proj",'charset':"utf8"}
    mydb=connect(opt)
    res=query(mydb,"SELECT * FROM users")
