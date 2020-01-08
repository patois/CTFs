# Solution for X-MAS CTF 2019 "Emu 2.0" challenge

* Opens and emulates "rom" file (must be in same directory when run)
* Contains disassembler and minimalistic debugger ("--debug" command line argument)
* flag is output to virtual "serial" device (redirected to file)

## Example Output
```
emu.py --debug
>
Unsupported command. Type 'h' for help.
> h
[h]elp, [d]isasm, [r]regs, [s]tep, [c]ont, [q]uit
> d
100h: 02 43     xor     A, 43h
> s
102h: 42 6e     bo      26eh
> s
104h: 00 ff     add     A, ffh
> s
106h: d1 10     ldmxor  A, [110h]
> s
108h: c1 10     frobn   [110h]
> s
10ah: 00 ff     add     A, ffh
> r
PC:     10ah
A:      42h
```