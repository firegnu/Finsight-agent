.PHONY: help install seed dev-backend dev-frontend test build serve-prod clean

help:
	@echo "FinSight Agent — 常用命令"
	@echo ""
	@echo "  make install        安装后端 + 前端全部依赖"
	@echo "  make seed           生成模拟数据（data/finsight.db）"
	@echo "  make dev-backend    启动 FastAPI 开发服务器（:8000）"
	@echo "  make dev-frontend   启动 Vite 开发服务器（:5173）"
	@echo "  make test           运行后端 pytest 全部用例"
	@echo "  make build          前端生产构建（frontend/dist/）"
	@echo "  make serve-prod     生产模式：build 前端 + 单进程启动（:8000 同时服务 API + 静态）"
	@echo "  make clean          清理构建产物 + SQLite"
	@echo ""
	@echo "开发模式：install → seed → 两个终端分别跑 dev-backend 和 dev-frontend"
	@echo "生产预览：install → seed → make serve-prod，访问 http://localhost:8000"

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

seed:
	python scripts/seed_data.py

dev-backend:
	uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	python -m pytest backend/tests/ -v

build:
	cd frontend && npm run build

serve-prod: build
	uvicorn backend.main:app --port 8000 --host 0.0.0.0

clean:
	rm -rf frontend/dist frontend/node_modules/.vite
	rm -f data/finsight.db data/finsight_test.db
