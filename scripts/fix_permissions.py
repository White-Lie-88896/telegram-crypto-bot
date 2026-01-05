#!/usr/bin/env python3
"""
文件权限修复脚本
修复数据库、日志和配置文件的权限，提升安全性
"""
import os
import stat
from pathlib import Path

def fix_database_permissions():
    """修复数据库文件权限 -> 600 (rw-------)"""
    db_path = Path('/opt/tgbotbinance/data/crypto_bot.db')

    if db_path.exists():
        try:
            # 设置为 600 (rw-------)
            os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)
            print(f"✓ Fixed permissions for {db_path}: 600 (rw-------)")
        except PermissionError as e:
            print(f"✗ Permission denied for {db_path}: {e}")
            print(f"  Please run: sudo chmod 600 {db_path}")
    else:
        print(f"ℹ Database file not found: {db_path}")

def fix_log_directory_permissions():
    """修复日志目录和文件权限 -> 700/600"""
    log_dir = Path('/opt/tgbotbinance/logs')

    if log_dir.exists():
        try:
            # 设置目录为 700 (rwx------)
            os.chmod(log_dir, stat.S_IRWXU)
            print(f"✓ Fixed permissions for {log_dir}: 700 (rwx------)")

            # 修复日志文件权限为 600
            for log_file in log_dir.glob('*.log'):
                try:
                    os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)
                    print(f"✓ Fixed permissions for {log_file}: 600 (rw-------)")
                except PermissionError as e:
                    print(f"✗ Permission denied for {log_file}: {e}")
        except PermissionError as e:
            print(f"✗ Permission denied for {log_dir}: {e}")
            print(f"  Please run: sudo chmod 700 {log_dir}")
    else:
        print(f"ℹ Log directory not found: {log_dir}")

def fix_env_file_permissions():
    """修复.env文件权限 -> 600"""
    env_path = Path('/opt/tgbotbinance/.env')

    if env_path.exists():
        try:
            # 设置为 600 (rw-------)
            os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
            print(f"✓ Fixed permissions for {env_path}: 600 (rw-------)")
        except PermissionError as e:
            print(f"✗ Permission denied for {env_path}: {e}")
            print(f"  Please run: sudo chmod 600 {env_path}")
    else:
        print(f"ℹ .env file not found: {env_path}")

def check_current_permissions():
    """检查当前文件权限"""
    print("\n" + "=" * 60)
    print("Current File Permissions Check:")
    print("=" * 60)

    files_to_check = [
        Path('/opt/tgbotbinance/.env'),
        Path('/opt/tgbotbinance/data/crypto_bot.db'),
        Path('/opt/tgbotbinance/logs'),
    ]

    for file_path in files_to_check:
        if file_path.exists():
            mode = oct(file_path.stat().st_mode)[-3:]
            print(f"  {file_path}: {mode}")
        else:
            print(f"  {file_path}: NOT FOUND")

    print("=" * 60)

if __name__ == '__main__':
    print("=" * 60)
    print("File Permissions Fix Script")
    print("=" * 60)
    print()

    # 检查当前权限
    check_current_permissions()

    print("\nFixing file permissions...")
    print()

    # 修复权限
    fix_database_permissions()
    fix_log_directory_permissions()
    fix_env_file_permissions()

    print()
    print("=" * 60)
    print("Permission fix completed!")
    print("=" * 60)
    print()

    # 再次检查
    check_current_permissions()
