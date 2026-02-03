# 多阶段构建：后端 Flask 应用
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到临时目录
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产阶段
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制安装的包
COPY --from=builder /root/.local /root/.local

# 确保脚本在 PATH 中
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动命令（使用 gunicorn 生产环境服务器）
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
