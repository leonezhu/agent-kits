#!/bin/bash
# Laya 一键环境（Python 3.10/3.11）
PY=$(command -v python3.11 || command -v python3.10 || command -v python3)
echo "用 $PY 建 venv: laya_venv"
$PY -m venv laya_venv
source laya_venv/bin/activate
pip install --upgrade pip -q
# 国内网络加速（公司网络慢就留着）
pip install laya -i https://pypi.tuna.tsinghua.edu.cn/simple -q || pip install laya -q
python -c "import laya; print('✅ laya OK:', [x for x in dir(laya) if not x.startswith('_')][:5], '...')"
echo "下一步: source laya_venv/bin/activate && python laya_demo.py"
