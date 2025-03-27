FROM python:3.9

# 安装 Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

COPY . .

# 设置 npm 源为官方源
RUN npm config set registry https://registry.npmjs.org/

RUN npm install
RUN pip install --no-cache-dir -r requirements.txt

# docker build -t spider_xhs .
# docker run -it spider_xhs bash