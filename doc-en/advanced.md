[Chinese README](/README.md) | [English README](/doc-en/README.md)


# Custom Data Tape

Edit `data_tape_maker.py` and modify the return value of the `make(dp)` function to change the initial data tape generation logic:

```python
# 返回斐波那契序列 parity
def make(dp):
    a, b = 0, 1
    for _ in range(dp):
        a, b = b, a + b
    return a % 2
```

By default, it returns a data tape filled with all 0s.

# Using the `r` Instruction for Addressing
The `r` instruction is defined to return to the beginning of the data tape. Therefore, `r` can be treated as a base value to implement base-plus-offset addressing, as in `r>*1024`.

You can use this feature to implement stacks and variables. You can even manually define data areas, variable areas, and stack areas, and use `r` and `>` to jump between them.


# Clever Uses of `fs`

The `f` instruction can only skip a single instruction, not multiple ones. This is a limitation of the `f` instruction. However, we can combine `f` and `s` instructions to work around this limitation.

## Switching to a Specified Program Tape

```
#0
r>*1024fs ...
#1
r...
```

The inherent limitation of the `s` instruction is that it can only switch to the next program tape in the queue by default. However, we can use specific flag bits and the `fs` instruction to achieve the ability to switch to a specified program tape.

In this program, I treat bit 1024 of the data tape as a flag bit. If bit 1024 of the data tape is 1, it switches to program tape 1; otherwise, it continues executing the current program tape.

This achieves the functionality of switching to a specified program tape.

# Using the `p` Instruction for GC

Assume the current data tape and read/write head are as follows: `[0]00011111`. If we want to discard a bunch of leading 0s, we can use the `p` instruction to cut the data tape and append it to the program tape sequence, thereby clearing the leading 0s.

```
#0
>x>>>
p
```

Because the `p` instruction treats the current data tape segment as a program, we need to set the first four bits of the current tape to `0100` (`s`). When executed, this will immediately switch tapes, thus protecting the subsequent chaotic data from being parsed.

In reality, this should not be considered full garbage collection, as it merely cuts the data tape and appends it to the program tape sequence without actually clearing the occupied space.

Note that this will break the origin point of the data tape, causing hard-coded addressing based on the `r` instruction to fail. This needs to be handled manually.
