[Chinese README](/README.md) | [English README](/doc-en/README.md)

# Demo Programs

## Set all cells of the chaotic data tape to zero

```
#0
f x x > l
```

## Simple demonstration of a dead loop with a dual-program tape

Used to show how to write multi-program tapes and the `s` instruction.

```
#0
ns
#1
ns
```

## Hello World ASCII encoding output

Each line represents an 8-bit ASCII code for a character being written.
`b` truncates the data tape for output, and `!` halts the machine immediately.

```
#0
(>x>>)*2(>)*2
(>x)*2(>)*3x(>)*2x>
(>x>x>)*2(>)*2
(>x>x>)*2(>)*2
(>x>x>)*2(x>)*2
(>)*2x(>>>)*2
(>x>)*3(x>)*2
(>x>x>)*2(x>)*2
(>x)*3(>)*3x(>)*2
(>x>x>)*2(>)*2
(>x)*2(>)*3x(>)*3
b
!
```
