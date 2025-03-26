#!/bin/bash

# 确保脚本在错误时停止
set -e

echo "开始部署 Spider_XHS..."

# 1. 拉取最新代码
echo "拉取最新代码..."
git pull

# 2. 构建并启动Docker容器
echo "构建并启动Docker容器..."
docker-compose up -d --build

# 3. 检查容器状态
echo "检查容器状态..."
docker ps | grep spider_xhs

echo "部署完成！" 