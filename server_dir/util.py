import logging
import yaml

#日志环境配置
def console_out(logFilename,log_level):
    ''''' Output log to file and console '''
    # Define a Handler and set a format which output to file

    logging.basicConfig(
        level=logging.DEBUG,  # 定义输出到文件的log级别，大于此级别的都被输出
        format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',  # 定义输出log的格式
        datefmt='%Y-%m-%d %A %H:%M:%S',  # 时间
        filename=logFilename,  # log文件名
        filemode='w')  # 写入模式“w”或“a”
    # Define a Handler and set a format which output to console
    console = logging.StreamHandler()  # 定义console handler
    console.setLevel(log_level)  # 定义该handler级别
    formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  # 定义该handler格式
    console.setFormatter(formatter)
    # Create an instance
    logging.getLogger().addHandler(console)  # 实例化添加handler
    return logging

#yaml文件读取
def yaml_conf():
    YAML_PATH = '../config.yaml'
    conf = open(file=YAML_PATH, mode='r', encoding='utf-8')
    conf = conf.read()
    # 这里使用yaml.Load方法将读取的结果传入进去
    conf = yaml.load(stream=conf, Loader=yaml.FullLoader)
    return conf

def log_level_switch(arg:str):
    arg=arg.upper()
    sw={"DEBUG":logging.DEBUG,"INFO":logging.INFO,"WARN":logging.WARNING,"WARNING":logging.WARNING,"ERROR":logging.ERROR,
        "CRITICAL":logging.CRITICAL}
    return sw.get(arg,logging.INFO)

CONF=yaml_conf()
LOGGER=console_out(CONF['app']['log_path'],log_level_switch(CONF['app']['log_level']))

