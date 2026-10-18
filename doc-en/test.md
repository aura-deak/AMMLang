[中文 README](/README.md) | [English README](/doc-en/README.md)

# Running Tests

The unit tests are located in the `test/` directory. They use the Python standard library `unittest` and require no additional dependencies. The tests cover the assembler, executor, all 10 instructions, and edge cases, totaling 60 test cases.

## Using uv

```bash
# 全部发现并运行
uv run python3 -m unittest discover -s test

# 分别运行汇编器 / 执行器测试
uv run python3 test/test_asm.py
uv run python3 test/test_vm.py

# 详细模式
uv run python3 -m unittest discover -s test -v
```

## Using pytest (dev dependency group)

```bash
uv run pytest test/ -v --cov=.
```

If all tests pass, the output will look like this:

```
Ran 60 tests in 0.004s
OK
```
