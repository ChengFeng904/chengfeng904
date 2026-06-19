"""
运行所有单元测试的统一入口。使用方式：
    cd /workspace/stock_research_system
    python -m tests.run           # 普通模式
    python -m tests.run --verbose # 详尽模式
    python -m tests.run --failfast # 遇到失败立即停止
"""

import argparse
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="运行股票投研系统单元测试")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    parser.add_argument("--failfast", action="store_true", help="失败后立即停止")
    parser.add_argument("--pattern", default="test_*.py", help="测试文件匹配模式")
    args = parser.parse_args()

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    loader = unittest.TestLoader()
    suite = loader.discover(tests_dir, pattern=args.pattern)

    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=args.failfast)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
