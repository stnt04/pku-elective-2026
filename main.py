#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: main.py
# modified: 2019-09-11

from ensure_deps import ensure   # 先自动检查/安装缺失依赖
ensure()

from autoelective.cli import run

if __name__ == '__main__':
    run()
