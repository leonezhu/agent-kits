# Laya 本地接入包

Jev 的开源复刻（Apache 2.0），本地跑的 System 1 判断引擎。
repo: https://github.com/NandhaKishorM/laya

## 文件
- `workclaw_laya_integration.py` — WorkClaw 集成骨架（Tool Gate + Router 两个函数，含注释）
- `laya_demo.py` — 四场景效果测试（晨报分类/safe_commit/上游路由/行为哨）
- `laya_test.py` — 邮件分诊原始 demo
- `setup_env.sh` — 一键环境脚本

## 公司电脑快速开始
```bash
unzip laya_local_kit.zip && cd laya_pkg_upload
bash setup_env.sh          # 建 venv + 装包（清华源）
source laya_venv/bin/activate
python laya_demo.py        # 验证跑通（首次会下载 2.2GB 权重）
```

公司网络下载权重慢/被墙：
```bash
export HF_ENDPOINT=https://hf-mirror.com
python laya_demo.py
```

## 已知坑（Mac x86_64 实测）
- Python 必须 3.10/3.11（torch 2.2 的 dynamo 不支持 3.12+）
- Mac 无 NVIDIA 卡必须 device="cpu"（MPS autocast 会炸）
- transformers 依赖冲突时锁 `transformers==4.48.0 numpy<2`
- 首次 load 30-60s（2.2GB 权重），进程内做单例

## 直接下载 zip
```
laya-local-kit/laya_local_kit.zip   # 6.3KB, 5个文件
```
或命令行:
```bash
curl -LO https://github.com/leonezhu/agent-kits/raw/main/laya-local-kit/laya_local_kit.zip
unzip laya_local_kit.zip && bash setup_env.sh
```
