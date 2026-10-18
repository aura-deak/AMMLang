[Chinese README](/README.md) | [English README](/doc-en/README.md)

# Toolchain Usage

## Installation

For global installation as a command-line tool (recommended):

```bash
uv tool install --python-preference only-system .
```

Or use the Arch package manager directly: `yay -S mmlang`

### Development Mode

Run the source code directly from the repository, suitable for development and debugging:

```bash
uv sync
uv run python3 asm.py
```


### File Descriptions

| File                       | Purpose                                       |
| :----------------------- | :--------------------------------------- |
| `asm.py` / `asm_core.py` | Assembler: Converts `.mmlang` source code to `.mmbin`           |
| `run.py` / `vm_core.py`  | Executor: Loads `.mmbin` and simulates its execution                    |
| `debug.py`               | Breakpoint Debugger: Uses `n` instructions as breakpoints, supporting step-into / continue to next breakpoint / run to completion |
| `common.py`              | Shared Module: Instruction encoding table, disassembly table, and bitarray utility functions            |
| `data_tape_maker.py`     | Data Tape Generator: Users can customize the initial data tape logic                     |
| `test/`                  | Unit Tests: Uses Python's standard `unittest`, covering all 10 instructions |

## Text → MMLang Source Code

```bash
mmlang-text2mm
```

Input a piece of text to automatically generate the corresponding MMLang source file. In development mode, use `uv run python3 text2mm.py`.

## Assemble `.mmlang` → `.mmbin`

```bash
mmlang-asm
```

Scans all `.mmlang` files in the current directory. If there is only one, it is assembled directly; if there are multiple, you will be prompted to enter a number to select one. The output is a `.mmbin` file with the same name. In development mode, use `uv run python3 asm.py`.

## Execute `.mmbin`

```bash
mmlang-run
```

Scans for `.mmbin` files in the current directory and executes them. When the `b` instruction is encountered, the program halts and outputs the truncated binary result sequence. In development mode, use `uv run python3 run.py`.

## Breakpoint Debugging

```bash
mmlang-debug
```

In development mode, use `uv run python3 debug.py`.

### Breakpoint Markers

Insert a `n` (no-operation) instruction into the `.mmlang` source code to use it as a breakpoint marker. `n` is already a no-operation instruction, so it does not affect the program's semantics; it simply causes the debugger to pause.

```
#0
>x>x>n>>x>x>nb!  ← 第一个 n 是断点，第二个 n 是另一个断点
```

### Interactive Commands

After starting, the debugger will pause **every time an `n` instruction is encountered** or when the program halts, displaying the complete tape state. You can use the following commands to control execution:

| Command                | Description                               |
| :---------------- | :------------------------------- |
| `Enter` / `n`     | **Step Into**: Executes one instruction                    |
| `c` / `continue`  | **Continue**: Runs to the next breakpoint (`n` instruction) or halt             |
| `r` / `run`       | **Run to End**: Runs directly to the end of the program, skipping all breakpoints            |
| `q` / `quit`      | **Quit**: Stops debugging and returns to the shell                |
| `h` / `help`      | Displays help                             |

### Display Content

- A disassembled view of all program tapes, with the current execution position highlighted by `[指令]`
- The contents of the data tape, with the cell below the read/write head highlighted by `[值]`
- The current PC (program tape position), DP (data tape position), and the number of steps executed

### Halt Output

After the program ends (due to a `!` instruction or the end of the tape), the debugger will print:

```
程序结束, 总步数: 15
最终输出 (b 指令): 0110011
ASCII 解码: ...              ← 仅当输出可解析为可打印 ASCII 时显示
```
