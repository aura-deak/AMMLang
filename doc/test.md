[中文 README](/README.md) | [English README](/doc-en/README.md)

# 运行测试

单元测试位于 `test/` 目录下，使用 Python 标准库 `unittest`，无需安装额外依赖。覆盖汇编器、执行器、全部 10 条指令及边界条件，共 60 个测试用例。

## 使用 uv

```bash
# 全部发现并运行
uv run python3 -m unittest discover -s test

# 分别运行汇编器 / 执行器测试
uv run python3 test/test_asm.py
uv run python3 test/test_vm.py

# 详细模式
uv run python3 -m unittest discover -s test -v
```

## 使用 pytest（dev dependency group）

```bash
uv run pytest test/ -v --cov=.
```

如果全部通过，输出类似：

```
Ran 60 tests in 0.004s
OK
```