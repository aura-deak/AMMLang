[中文 README](/README.md) | [English README](/doc-en/README.md)

# Mobiours Machine & AMMLang

> [!NOTE]
原名为`Mobius Machine & MMLang`，但是Mobius Machine和MMLang都已经存在，故改名。


这台机器被叫作莫比奥尔斯机（Mobiours Machine），它的专属编程语言被称为莫比奥尔斯机编程语言（Aura's Mobiours Machine programming Language）

莫比奥尔斯机融合了图灵机、冯·诺伊曼机、哈佛架构，等等。

莫比奥尔斯机的结构极其简单，不需要ALU、寄存器和状态转移表，电子控制部件结构非常简单，却可以实现现代计算机的一些特性，并执行通用计算任务。而代价是让程序员完成本来应当由硬件完成的工作。它可能是最适合从零手搓的图灵机变体之一。

我在探究计算机发展的时候创造了它，它的很多逻辑都来源于历史上真实存在过的那些机器，如首尾相连实现循环的程序纸带、多程序纸带切换、以及那个蛮荒年代里对代码自生成的大胆探索。

理论上，这应当属于一次对计算模型边界的探讨，而不仅仅是创造了一个esolang。

MMLang相比其他的esolang最大的不同在于，**它的困难不是被设计的，而是由它的硬件结构决定的**，它将简陋的硬件结构无抽象地暴露给程序员。

## AMMLang文档阅读目录

- [莫比乌斯机概念、MMLang指令集与语法](doc/mobius-machine-and-MMLang.md)
- [工具链用法](doc/tools.md)
- [高级特性、高级编程技巧](doc/advanced.md)
- [程序示例](doc/examples.md)
- [工具链的单元测试](doc/test.md)
- [English documentation](doc-en/README.md)

**必读**：AMMLang指令集与语法、工具链用法。或阅读下面的文档快速开始。

## Quick Start

将以hello world为例，展示AMMLang的基本用法。

### 1. 安装 uv

[uv](https://docs.astral.sh/uv/) 是一个现代的 Python 包管理器，用于依赖管理和环境隔离。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装 AMMLang 工具链

> [!NOTE]
> Arch 用户可直接使用 `yay -S mmlang` 并跳过本步骤。
>
> 若之前通过 uv 安装过 mmlang，再切换到 yay 方式前请务必先 `uv tool uninstall mmlang`。

将 AMMLang 安装为全局命令，可在任何地方直接调用：

```bash
git clone https://github.com/aura-deak/AMMLang.git
cd MMLang
uv tool install --python-preference only-system .
```

安装后即可使用 `mmlang-asm`、`mmlang-run`、`mmlang-debug`、`mmlang-text2mm` 命令。

### 3. 编译与执行 hello world

```bash
mmlang-text2mm       # 输入 hello world，生成 hello_world.mmlang
mmlang-asm           # 自动发现并汇编，生成 hello_world.mmbin
mmlang-run           # 执行 .mmbin，打印结果
```

### 4. 卸载

```bash
uv tool uninstall mmlang
```