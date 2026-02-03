#!/bin/bash
# QYQuant Docker 一键部署脚本
# 支持 Linux 和 macOS

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    print_info "Docker 环境检查通过"
}

# 检查并创建 .env 文件
check_env_file() {
    if [ ! -f .env ]; then
        print_warn ".env 文件不存在，从 .env.example 复制..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_info "已创建 .env 文件，请修改其中的配置（特别是密码和密钥）"
            read -p "是否现在编辑 .env 文件？(y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ${EDITOR:-nano} .env
            fi
        else
            print_error ".env.example 文件不存在"
            exit 1
        fi
    else
        print_info "使用现有的 .env 文件"
    fi
}

# 构建镜像
build_images() {
    print_info "开始构建 Docker 镜像..."
    docker-compose build --no-cache
    print_info "镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动所有服务..."
    docker-compose up -d

    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    print_info "服务状态："
    docker-compose ps
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."

    # 运行数据库迁移
    docker-compose exec -T backend flask db upgrade || print_warn "数据库迁移失败（可能已经执行过）"

    # 创建默认管理员账号
    docker-compose exec -T backend python -c "
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@qyquant.com'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('默认管理员账号已创建: admin / admin123')
    else:
        print('管理员账号已存在')
" || print_warn "创建管理员账号失败"
}

# 显示访问信息
show_access_info() {
    FRONTEND_PORT=$(grep FRONTEND_PORT .env | cut -d '=' -f2)
    BACKEND_PORT=$(grep BACKEND_PORT .env | cut -d '=' -f2)

    echo ""
    echo "============================================"
    print_info "部署完成！"
    echo "============================================"
    echo -e "前端地址: ${GREEN}http://localhost:${FRONTEND_PORT:-80}${NC}"
    echo -e "后端 API: ${GREEN}http://localhost:${BACKEND_PORT:-5000}${NC}"
    echo -e "默认账号: ${GREEN}admin / admin123${NC}"
    echo ""
    print_warn "生产环境请立即修改默认密码！"
    echo ""
    echo "常用命令："
    echo -e "  查看日志: ${GREEN}docker-compose logs -f${NC}"
    echo -e "  停止服务: ${GREEN}docker-compose down${NC}"
    echo -e "  重启服务: ${GREEN}docker-compose restart${NC}"
    echo -e "  查看状态: ${GREEN}docker-compose ps${NC}"
    echo "============================================"
}

# 主流程
main() {
    echo "============================================"
    echo "       QYQuant Docker 一键部署脚本"
    echo "============================================"
    echo ""

    check_docker
    check_env_file

    echo ""
    read -p "是否开始构建和部署？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        exit 0
    fi

    build_images
    start_services
    init_database
    show_access_info
}

# 执行主流程
main
