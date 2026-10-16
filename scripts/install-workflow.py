#!/usr/bin/env python3
"""保留旧命令参数，只提示 SuperBeiTeam 独立安装入口。"""
import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', choices=['codex', 'hermes'])
    parser.add_argument('--home', help='兼容参数；本入口不再修改宿主配置')
    parser.add_argument('--rollback', help='旧安装回执；本入口不再执行回退')
    args = parser.parse_args()
    if args.rollback and (args.tool or args.home):
        parser.error('--rollback 不与安装参数同时使用')
    if not args.rollback and not args.tool:
        parser.error('请提供原命令的 --tool 或 --rollback 参数')
    print('团队安装已迁至 SuperBeiTeam（私有仓库，需要访问权限）：')
    print('https://github.com/NBStarry/SuperBeiTeam')
    print('本入口未修改任何配置，也未下载私有代码。请按 Team 安装说明单独安装。')
    if args.rollback:
        print('旧回执仍保留。请按 Team 的旧安装回退说明处理，不要删除备份。')


if __name__ == '__main__':
    main()
