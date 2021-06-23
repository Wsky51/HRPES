import docker

class DockerCient():
    def __init__(self):
        self.client = docker.DockerClient(base_url='unix://var/run/docker.sock', version="auto")

    #得到所有的docker images list
    def get_images(self):
        return self.client.images.list();
        # print(img.attrs["RepoTags"][0])

    #获取所有的containers对象列表
    def get_containers(self):
        # con1 = self.client.containers.list()[0]
        return self.client.containers.list()
        # print("container:" + container.name + " image:" + container.image.attrs["RepoTags"][0])
        # for container in docker_client.get_containers():
        #     # print(dir(container))
        #     print("container:" + container.name + " image:" + container.image.attrs["RepoTags"][0]+",containers.id:"+container.id)

    #获取所有的containers对象列表
    def get_container_byid(self,id):
        return self.client.containers.get(id)

    #拉取一个containers对象
    def pull_image(self,images_name,tag):
        return self.client.images.pull(repository=images_name,tag=tag)

# docker run --name=wuyi-mysql-pass -it -p 3308:3306 -e MYSQL_ROOT_PASSWORD=wuyi221013 -d mysql
#docker run --name wuyi-mysql-pass -p 3306:3306 -e MYSQL_ROOT_PASSWORD=12345 -d mysql:5.7.27
# 通过容器生成的iamges 运行备份时：
if __name__ == '__main__':
    client = docker.DockerClient(base_url='unix://var/run/docker.sock', version="auto")
    isok = client.containers.run("mysql",command=["environment MYSQL_ROOT_PASSWORD=wuyi221013"])
    print(isok)
    print(client.containers.list())