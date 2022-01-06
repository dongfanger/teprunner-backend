# teprunner-backend

B站：[teprunner测试平台视频教程全集](https://www.bilibili.com/video/BV1Kr4y1v7br/)

## 下载源码

方式①：

```
git clone git@github.com:dongfanger/teprunner-backend.git
```

方式②：下载zip压缩包后解压。

![image-20210821110533369](README/image-20210821110533369.png)

## 准备数据库连接

以下两者任选其一即可。

**SQLite**

SQLite数据库是Django自带的，不需要另外安装。由于会用到`models.JSONField`，SQLite默认不兼容，所以需要下载`sqlite3.dll`文件替换下：https://www.sqlite.org/download.html

根据Python版本选择相应文件，比如我的windows安装的Python38-32，下载了`sqlite-dll-win32-x86-3340100.zip`这个软件包，解压后将`D:\Program Files (x86)\Python38-32\DLLs\sqlite3.dll`替换。

**MySQL**

也可以使用MySQL数据库，前提是已经安装并创建好了数据库。修改mysite/settings.py中的数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '主机',
        'PORT': 端口,
        'NAME': '数据库名',
        'USER': '用户名',
        'PASSWORD': '密码'
    }
}
```

Django默认通过底层调用mysqlclient这个库和MySQL交互。但是mysqlclient非常不好安装，我们改用 pymysql。先安装pymysql：

```shell
pip install pymysql
```

然后在与mysite/settings.py文件同级的`__init__`文件中添加代码：

```python
import pymysql

pymysql.version_info = (1, 4, 0, "final", 0)
pymysql.install_as_MySQLdb()
```

## 迁移数据库

数据库准备好以后，就可以执行以下命令，创建表结构：

```shell
python manage.py makemigrations
python manage.py migrate
```

然后执行以下命令，初始化用户数据：

```shell
python manage.py loaddata user
```

## 启动服务

数据准备好了，执行以下命令，启动后端服务：

```
python manage.py runserver
```

启动成功后，确保前端服务也已解决启动成功后，就可以打开`localhost:8080`，输入用户名`admin`，密码`qa123456`登录测试平台体验啦。