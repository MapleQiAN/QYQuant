#!/usr/bin/env python3
"""
创建管理员账户脚本
用法: python scripts/create_admin.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.extensions import db
from app.models import User


def create_admin_user():
    """创建管理员账户"""
    app = create_app('development')

    with app.app_context():
        # 检查管理员是否已存在
        existing_admin = User.query.filter_by(phone='13800138000').first()
        if existing_admin:
            print(f"❌ 管理员账户已存在: {existing_admin.nickname} ({existing_admin.phone})")
            print(f"   当前角色: {existing_admin.role}")
            # 更新为管理员角色
            if existing_admin.role != 'admin':
                existing_admin.role = 'admin'
                db.session.commit()
                print(f"✅ 已将用户角色更新为: admin")
            return

        # 创建管理员用户
        admin = User(
            phone='13800138000',
            nickname='系统管理员',
            avatar_url='',
            bio='系统管理员，拥有所有权限',
            role='admin',
            plan_level='premium',  # 给管理员高级会员权限
            onboarding_completed=True,
            sim_disclaimer_accepted=True,
        )

        db.session.add(admin)
        db.session.commit()

        print("✅ 管理员账户创建成功!")
        print(f"   手机号: 13800138000")
        print(f"   昵称: {admin.nickname}")
        print(f"   角色: {admin.role}")
        print(f"   会员等级: {admin.plan_level}")
        print(f"   用户ID: {admin.id}")
        print("\n📝 登录方式:")
        print("   1. 使用手机号 13800138000 登录")
        print("   2. 开发环境下验证码固定为: 123456")
        print("   3. 生产环境请查看日志或配置文件获取验证码")


if __name__ == '__main__':
    create_admin_user()
