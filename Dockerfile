# 使用官方 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置容器内的工作目录
WORKDIR /app

# 先复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有代码到容器
COPY . .

# 默认命令：先显示容器已启动
CMD ["python", "--version"]