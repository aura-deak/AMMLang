[中文 README](/README.md) | [English README](/doc-en/README.md)

# 工具链用法

## 安装

全局安装为命令行工具（推荐）：

```bash
uv tool install --python-preference only-system .
```

或直接使用 Arch 包管理器：`yay -S mmlang`

### 开发模式

在仓库内直接运行源码，适合开发调试：

```bash
uv sync
uv run python3 asm.py
```


### 文件说明

| 文件                       | 用途                                       |
| :----------------------- | :--------------------------------------- |
| `asm.py` / `asm_core.py` | 汇编器：将 `.mmlang` 源码转换为 `.mmbin`           |
| `run.py` / `vm_core.py`  | 执行器：加载 `.mmbin` 并模拟运行                    |
| `debug.py`               | 断点调试器：以 `n` 指令为断点，支持单步 / continue 到下个断点 / run 到结束 |
| `common.py`              | 共享模块：指令编码表、反汇编表、bitarray 工具函数            |
| `data_tape_maker.py`     | 数据纸带生成器：用户可自定义初始数据纸带逻辑                     |
| `test/`                  | 单元测试：使用 Python 标准 `unittest`，覆盖全部 10 条指令 |

## 文本 → MMLang 源码

```bash
mmlang-text2mm
```

输入一段文本，自动生成对应的 MMLang 源文件。开发模式下使用 `uv run python3 text2mm.py`。

## 汇编 `.mmlang` → `.mmbin`

```bash
mmlang-asm
```

扫描当前目录下所有 `.mmlang` 文件；若唯一则直接汇编，若多个则提示输入序号选择。输出同名 `.mmbin` 文件。开发模式下使用 `uv run python3 asm.py`。

## 执行 `.mmbin`

```bash
mmlang-run
```

扫描当前目录下 `.mmbin` 文件并执行。遇到 `b` 指令停机时，输出截断后的二进制结果序列。开发模式下使用 `uv run python3 run.py`。

## 断点调试

```bash
mmlang-debug
```

开发模式下使用 `uv run python3 debug.py`。

### 断点标记

在 `.mmlang` 源码中插入 `n`（空操作）指令即可作为断点标记。`n` 原本就是空操作，不影响程序语义，仅让调试器暂停。

```
#0
>x>x>n>>x>x>nb!  ← 第一个 n 是断点，第二个 n 是另一个断点
```

### 交互命令

启动后调试器会在**每次遇到 n 指令**或停机时暂停，显示完整纸带状态。可用以下命令控制执行：

| 命令                | 说明                               |
| :---------------- | :------------------------------- |
| `Enter` / `n`     | **单步**：执行一条指令                    |
| `c` / `continue`  | **继续**：运行到下一个断点（n 指令）或停机             |
| `r` / `run`       | **到底**：直接运行到程序结束，跳过所有断点            |
| `q` / `quit`      | **退出**：停止调试，返回 shell                |
| `h` / `help`      | 显示帮助                             |

### 显示内容

- 所有程序纸带的反汇编视图，当前执行位置用 `[指令]` 高亮
- 数据纸带内容，读写头下方格子用 `[值]` 高亮
- 当前 PC（程序纸带位置）、DP（数据纸带位置）、已执行步数

### 停机输出

程序结束后（`!` 指令或纸带末尾）调试器会打印：

```
程序结束, 总步数: 15
最终输出 (b 指令): 0110011
ASCII 解码: ...              ← 仅当输出可解析为可打印 ASCII 时显示
```