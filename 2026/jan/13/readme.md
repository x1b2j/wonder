```
john@backtrack:~/wonder/2026/jan/12$ cat firstprog.c 
#include <stdio.h>

int main() {
  int i;
  for(i=0; i<10; i++) {          // Loop 10 times.
    printf("Hello, world!\n");   // put the string to the output.
  }
  return 0;                      // Tell OS the program exited without errors.
}
john@backtrack:~/wonder/2026/jan/12$ ./a.out 
Hello, world!
Hello, world!
Hello, world!
Hello, world!
Hello, world!
Hello, world!
Hello, world!
Hello, world!
Hello, world!
Hello, world!
john@backtrack:~/wonder/2026/jan/12$ gdb ./a.out 
GNU gdb (Ubuntu 15.0.50.20240403-0ubuntu1) 15.0.50.20240403-git
Copyright (C) 2024 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<https://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from ./a.out...
(gdb) info registers
The program has no registers now.
(gdb) info main
main
(gdb) break main
Breakpoint 1 at 0x1155: file firstprog.c, line 5.
(gdb) run
Starting program: /home/john/wonder/2026/jan/12/a.out 

This GDB supports auto-downloading debuginfo from the following URLs:
  <https://debuginfod.ubuntu.com>
Enable debuginfod for this session? (y or [n]) y
Debuginfod has been enabled.
To make this setting permanent, add 'set debuginfod enabled on' to .gdbinit.
Downloading separate debug info for system-supplied DSO at 0x7ffff7fc3000
[Thread debugging using libthread_db enabled]                                                                                                                           
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 1, main () at firstprog.c:5
5	  for(i=0; i<10; i++) {          // Loop 10 times.
(gdb) info registers
rax            0x555555555149      93824992235849
rbx            0x7fffffffdcd8      140737488346328
rcx            0x555555557dc0      93824992247232
rdx            0x7fffffffdce8      140737488346344
rsi            0x7fffffffdcd8      140737488346328
rdi            0x1                 1
rbp            0x7fffffffdbb0      0x7fffffffdbb0
rsp            0x7fffffffdba0      0x7fffffffdba0
r8             0x0                 0
r9             0x7ffff7fca380      140737353917312
r10            0x7fffffffd8d0      140737488345296
r11            0x203               515
r12            0x1                 1
r13            0x0                 0
r14            0x555555557dc0      93824992247232
r15            0x7ffff7ffd000      140737354125312
rip            0x555555555155      0x555555555155 <main+12>
eflags         0x206               [ PF IF ]
cs             0x33                51
ss             0x2b                43
ds             0x0                 0
es             0x0                 0
fs             0x0                 0
gs             0x0                 0
fs_base        0x7ffff7fa9740      140737353783104
gs_base        0x0                 0
(gdb) info register rip
rip            0x555555555155      0x555555555155 <main+12>
(gdb) x/x $rip
0x555555555155 <main+12>:	0x00fc45c7
(gdb) t/x $rip
Invalid thread ID: /x $rip
(gdb) x/t $rip
0x555555555155 <main+12>:	00000000111111000100010111000111
(gdb) x/2x $rip
0x555555555155 <main+12>:	0x00fc45c7	0xeb000000
(gdb) list
1	#include <stdio.h>
2	
3	int main() {
4	  int i;
5	  for(i=0; i<10; i++) {          // Loop 10 times.
6	    printf("Hello, world!\n");   // put the string to the output.
7	  }
8	  return 0;                      // Tell OS the program exited without errors.
9	}
(gdb) disassemble main
Dump of assembler code for function main:
   0x0000555555555149 <+0>:	endbr64
   0x000055555555514d <+4>:	push   rbp
   0x000055555555514e <+5>:	mov    rbp,rsp
   0x0000555555555151 <+8>:	sub    rsp,0x10
=> 0x0000555555555155 <+12>:	mov    DWORD PTR [rbp-0x4],0x0
   0x000055555555515c <+19>:	jmp    0x555555555171 <main+40>
   0x000055555555515e <+21>:	lea    rax,[rip+0xe9f]        # 0x555555556004
   0x0000555555555165 <+28>:	mov    rdi,rax
   0x0000555555555168 <+31>:	call   0x555555555050 <puts@plt>
   0x000055555555516d <+36>:	add    DWORD PTR [rbp-0x4],0x1
   0x0000555555555171 <+40>:	cmp    DWORD PTR [rbp-0x4],0x9
   0x0000555555555175 <+44>:	jle    0x55555555515e <main+21>
   0x0000555555555177 <+46>:	mov    eax,0x0
   0x000055555555517c <+51>:	leave
   0x000055555555517d <+52>:	ret
End of assembler dump.
(gdb) x/12x $rip
0x555555555155 <main+12>:	0x00fc45c7	0xeb000000	0x058d4813	0x00000e9f
0x555555555165 <main+28>:	0xe8c78948	0xfffffee3	0x01fc4583	0x09fc7d83
0x555555555175 <main+44>:	0x00b8e77e	0xc9000000	0xf30000c3	0x48fa1e0f
(gdb) x/18x $rip
0x555555555155 <main+12>:	0x00fc45c7	0xeb000000	0x058d4813	0x00000e9f
0x555555555165 <main+28>:	0xe8c78948	0xfffffee3	0x01fc4583	0x09fc7d83
0x555555555175 <main+44>:	0x00b8e77e	0xc9000000	0xf30000c3	0x48fa1e0f
0x555555555185 <_fini+5>:	0x4808ec83	0xc308c483	0x00000000	0x00000000
0x555555555195:	0x00000000	0x00000000
(gdb) x/8xw $rip
0x555555555155 <main+12>:	0x00fc45c7	0xeb000000	0x058d4813	0x00000e9f
0x555555555165 <main+28>:	0xe8c78948	0xfffffee3	0x01fc4583	0x09fc7d83
(gdb) x/8xh $rip
0x555555555155 <main+12>:	0x45c7	0x00fc	0x0000	0xeb00	0x4813	0x058d	0x0e9f	0x0000
(gdb) x/8xb $rip
0x555555555155 <main+12>:	0xc7	0x45	0xfc	0x00	0x00	0x00	0x00	0xeb
(gdb) x/4ub $rip
0x555555555155 <main+12>:	199	69	252	0
(gdb) x/1uw $rip
0x555555555155 <main+12>:	16532935
(gdb) quit
A debugging session is active.

	Inferior 1 [process 3678] will be killed.

Quit anyway? (y or n) y
john@backtrack:~/wonder/2026/jan/12$ bc -ql
199*(256^3)+69*(256^2)+252*(256^1)+0*(256^0)
3343252480
0*(256^3)+252*(256^2)+69*(256^1)+199*(256^0)
16532935
quit
john@backtrack:~/wonder/2026/jan/12$ gdb -q ./a.out 
Reading symbols from ./a.out...
(gdb) break main
Breakpoint 1 at 0x1155: file firstprog.c, line 5.
(gdb) run
Starting program: /home/john/wonder/2026/jan/12/a.out 
Downloading separate debug info for system-supplied DSO at 0x7ffff7fc3000
[Thread debugging using libthread_db enabled]                                                                                                                           
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 1, main () at firstprog.c:5
5	  for(i=0; i<10; i++) {          // Loop 10 times.
(gdb) i r $eip
Invalid register `eip'
(gdb) i r $rip
rip            0x555555555155      0x555555555155 <main+12>
(gdb) x/i $rip
=> 0x555555555155 <main+12>:	mov    DWORD PTR [rbp-0x4],0x0
(gdb) x/3i $rip
=> 0x555555555155 <main+12>:	mov    DWORD PTR [rbp-0x4],0x0
   0x55555555515c <main+19>:	jmp    0x555555555171 <main+40>
   0x55555555515e <main+21>:	lea    rax,[rip+0xe9f]        # 0x555555556004
(gdb) x/7xb $rip
0x555555555155 <main+12>:	0xc7	0x45	0xfc	0x00	0x00	0x00	0x00
(gdb) x/i $rip
=> 0x555555555155 <main+12>:	mov    DWORD PTR [rbp-0x4],0x0
(gdb) i r rbp
rbp            0x7fffffffdbb0      0x7fffffffdbb0
(gdb) x/4xb $rbp-4
0x7fffffffdbac:	0xff	0x7f	0x00	0x00
(gdb) x/4xb 0x7fffffffdbac
0x7fffffffdbac:	0xff	0x7f	0x00	0x00
(gdb) print $rbp-4
$1 = (void *) 0x7fffffffdbac
(gdb) x/4xb $1
0x7fffffffdbac:	0xff	0x7f	0x00	0x00
(gdb) x/xw $1
0x7fffffffdbac:	0x00007fff
(gdb) nexti
5	  for(i=0; i<10; i++) {          // Loop 10 times.
(gdb) x/4xb $1
0x7fffffffdbac:	0x00	0x00	0x00	0x00
(gdb) x/xw $1
0x7fffffffdbac:	0x00000000
(gdb) i r $rip
rip            0x55555555515c      0x55555555515c <main+19>
(gdb) x/i $rip
=> 0x55555555515c <main+19>:	jmp    0x555555555171 <main+40>
(gdb) x/10i $rip
=> 0x55555555515c <main+19>:	jmp    0x555555555171 <main+40>
   0x55555555515e <main+21>:	lea    rax,[rip+0xe9f]        # 0x555555556004
   0x555555555165 <main+28>:	mov    rdi,rax
   0x555555555168 <main+31>:	call   0x555555555050 <puts@plt>
   0x55555555516d <main+36>:	add    DWORD PTR [rbp-0x4],0x1
   0x555555555171 <main+40>:	cmp    DWORD PTR [rbp-0x4],0x9
   0x555555555175 <main+44>:	jle    0x55555555515e <main+21>
   0x555555555177 <main+46>:	mov    eax,0x0
   0x55555555517c <main+51>:	leave
   0x55555555517d <main+52>:	ret
(gdb) nexti
0x0000555555555171	5	  for(i=0; i<10; i++) {          // Loop 10 times.
(gdb) i r $rip
rip            0x555555555171      0x555555555171 <main+40>
(gdb) x/i $rip
=> 0x555555555171 <main+40>:	cmp    DWORD PTR [rbp-0x4],0x9
(gdb) nexti
0x0000555555555175	5	  for(i=0; i<10; i++) {          // Loop 10 times.
(gdb) i r $rip
rip            0x555555555175      0x555555555175 <main+44>
(gdb) x/i $rip
=> 0x555555555175 <main+44>:	jle    0x55555555515e <main+21>
(gdb) nexti
6	    printf("Hello, world!\n");   // put the string to the output.
(gdb) x/i $rip
=> 0x55555555515e <main+21>:	lea    rax,[rip+0xe9f]        # 0x555555556004
(gdb) i r $rip
rip            0x55555555515e      0x55555555515e <main+21>
(gdb) disassemble main
Dump of assembler code for function main:
   0x0000555555555149 <+0>:	endbr64
   0x000055555555514d <+4>:	push   rbp
   0x000055555555514e <+5>:	mov    rbp,rsp
   0x0000555555555151 <+8>:	sub    rsp,0x10
   0x0000555555555155 <+12>:	mov    DWORD PTR [rbp-0x4],0x0
   0x000055555555515c <+19>:	jmp    0x555555555171 <main+40>
=> 0x000055555555515e <+21>:	lea    rax,[rip+0xe9f]        # 0x555555556004
   0x0000555555555165 <+28>:	mov    rdi,rax
   0x0000555555555168 <+31>:	call   0x555555555050 <puts@plt>
   0x000055555555516d <+36>:	add    DWORD PTR [rbp-0x4],0x1
   0x0000555555555171 <+40>:	cmp    DWORD PTR [rbp-0x4],0x9
   0x0000555555555175 <+44>:	jle    0x55555555515e <main+21>
   0x0000555555555177 <+46>:	mov    eax,0x0
   0x000055555555517c <+51>:	leave
   0x000055555555517d <+52>:	ret
End of assembler dump.
(gdb) i r rsp
rsp            0x7fffffffdba0      0x7fffffffdba0
(gdb) x/x $rax
0x555555555149 <main>:	0xfa1e0ff3
(gdb) x 0x555555555050
0x555555555050 <puts@plt>:	0xfa1e0ff3
(gdb) x/2x 0x555555555050
0x555555555050 <puts@plt>:	0xfa1e0ff3	0x2f7625ff
(gdb) x/3x 0x555555555050
0x555555555050 <puts@plt>:	0xfa1e0ff3	0x2f7625ff	0x0f660000
(gdb) x/6x 0x555555555050
0x555555555050 <puts@plt>:	0xfa1e0ff3	0x2f7625ff	0x0f660000	0x0000441f
0x555555555060 <_start>:	0xfa1e0ff3	0x8949ed31
(gdb) x/s 0x555555555050
0x555555555050 <puts@plt>:	"\363\017\036\372\377%v/"
(gdb) 
```




Perfect! This shows a **real-world example** from `gdb` output. Let me analyze this complete sequence:

## **Complete Context:**
```assembly
0x55555555515e <+21>:  lea    rax, [rip+0xe9f]        # Load address of string
0x555555555165 <+28>:  mov    rdi, rax               # Move address to 1st arg register
0x555555555168 <+31>:  call   0x555555555050 <puts@plt>  # Call puts()
```

## **What's Happening:**
1. **Line 1:** Calculate the address of a string constant
   - `rip` at `0x55555555515e` + 7 (instruction length) = `0x555555555165`
   - `0x555555555165 + 0xe9f = 0x555555556004`
   - The comment confirms: `# 0x555555556004`

2. **Line 2:** Prepare for function call
   - Move the calculated address into `rdi` (first argument register for System V ABI)

3. **Line 3:** Call `puts()` through the PLT (Procedure Linkage Table)
   - Prints the string at address `0x555555556004`

## **What's at 0x555555556004?**
Almost certainly a **string constant** in the `.rodata` (read-only data) section. You can check with:
```bash
# In gdb:
(gdb) x/s 0x555555556004
# Or to see as hex:
(gdb) x/32xb 0x555555556004
```

## **Example String:**
If you examine that address, you might see something like:
```
0x555555556004: "Hello, World!\n"
0x555555556013: <next data or string>
```

## **Why This Pattern?**
This is the standard way to pass string literals to functions in position-independent executables (PIE):
1. **RIP-relative addressing** allows the code to work at any load address
2. **String literals** are stored in `.rodata` section
3. `puts()` expects a pointer to a null-terminated string in `rdi`

## **Equivalent C code:**
```c
puts("Hello, World!");  // Compiler stores the string in .rodata
```

## **Memory Layout:**
```
.text section (code):    0x555555555000 - 0x555555555xxx
.rodata section (data):  0x555555556000 - 0x555555556xxx
```
The offset `0xe9f` (3743 bytes) shows the distance between the code and data sections.

This is a classic example of **position-independent code** accessing **constant data**!
