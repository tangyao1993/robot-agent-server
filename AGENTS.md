# Repository Guidelines

## 项目结构与模块组织
项目源代码集中在 `src/`：`main.py` 是入口，负责装配 `network`、`processors`、`workflow` 与 `database` 模块，异步启动 WebSocket 服务。`network/` 管理会话与消息流转，`processors/` 提供音频处理、ASR 与 TTS，`workflow/` 通过 LangGraph 定义对话状态机，`database/operations.py` 实现 MySQL 异步访问。运行时音频会落在 `assets/audio_files/`（如不存在会自动创建），依赖声明在 `requirements.txt`。

## 构建、测试与开发命令
- `python -m venv .venv && source .venv/bin/activate`：创建并激活虚拟环境。
- `pip install -r requirements.txt`：安装服务依赖。
- `python src/main.py`：从仓库根目录启动 WebSocket 服务。
- `pytest tests -q`：运行单元与集成测试（新增测试后执行）。

## 编码风格与命名约定
遵循 PEP 8：四空格缩进，模块、文件与函数采用 snake_case，类名使用 PascalCase。重点逻辑保持纯函数或独立类，便于异步组合；公共常量使用大写蛇形并集中声明。统一使用 `logging` 记录运行状态，避免裸 `print`。建议在新增模块时补充类型注解与精简 docstring，提交前可按需运行 `black` 或 `ruff` 保持格式一致。

## 测试指引
项目尚未内置测试套件，推荐以 pytest 与 pytest-asyncio 编写异步场景。测试文件放在 `tests/` 并命名 `test_<module>.py`，覆盖消息编排、LangGraph 节点与数据库交互；对 ASR/TTS 请求使用 mock 或本地假服务。目标覆盖率维持在 80% 以上，同时验证异常路径与日志输出。运行测试前可通过 `export PYTHONPATH=.` 保证导入路径一致。

## 提交与合并请求
遵循仓库现有祈使句式提交信息，例如 `fix audio timeout`、`add workflow guard`，每次提交聚焦单一语义。提交 PR 时附上改动摘要、测试结果与关联 Issue，接口或协议变更需补充示例报文或前后对比。涉及部署或配置调整时，请列出所需环境变量及迁移步骤，确保评审者可复现。

## 配置与安全提示
默认的数据库与 ASR/TTS 地址在源码中硬编码，开发或部署时务必以环境变量或 `.env` 覆写，例如 `export DB_HOST=...`、`export OLLAMA_BASE_URL=...`，必要时在入口模块读取。避免将真实凭证写入 Git 历史，公开环境需限制 WebSocket 来源并监控 `assets/audio_files/` 存储增长。
