```
john@backtrack:~/wonder/2026/jan/14$ cat char_array.c 
#include <stdio.h>
#include <string.h>

int main() {
  char str_a[20];
  strcpy(str_a, "Hello, world!\n");
  printf(str_a);
}
john@backtrack:~/wonder/2026/jan/14$ gcc -g -o char_array char_array.c 
char_array.c: In function ‘main’:
char_array.c:7:10: warning: format not a string literal and no format arguments [-Wformat-security]
    7 |   printf(str_a);
      |          ^~~~~
john@backtrack:~/wonder/2026/jan/14$ vim char_array.c 
john@backtrack:~/wonder/2026/jan/14$ ls
char_array  char_array.c
john@backtrack:~/wonder/2026/jan/14$ ./char_array 
Hello, world!
john@backtrack:~/wonder/2026/jan/14$ gdb ./char_array 
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
Reading symbols from ./char_array...
(gdb) list
1	#include <stdio.h>
2	#include <string.h>
3	
4	int main() {
5	  char str_a[20];
6	  strcpy(str_a, "Hello, world!\n");
7	  printf(str_a);
8	}
(gdb) quit
john@backtrack:~/wonder/2026/jan/14$ rm -f char_array
john@backtrack:~/wonder/2026/jan/14$ ls
char_array.c
john@backtrack:~/wonder/2026/jan/14$ vim char_array.c 
john@backtrack:~/wonder/2026/jan/14$ cat char_array.c 
#include <stdio.h>
#include <string.h>

int main() {
  char str_a[20];

  strcpy(str_a, "Hello, world!\n");
  printf(str_a);
}
john@backtrack:~/wonder/2026/jan/14$ gcc -g -o char_array char_array.c 
char_array.c: In function ‘main’:
char_array.c:8:10: warning: format not a string literal and no format arguments [-Wformat-security]
    8 |   printf(str_a);
      |          ^~~~~
john@backtrack:~/wonder/2026/jan/14$ vim char_array
john@backtrack:~/wonder/2026/jan/14$ vim char_array.c 
john@backtrack:~/wonder/2026/jan/14$ cat char_array.c 
#include <stdio.h>
#include <string.h>

int main() {
  char str_a[20];

  strcpy(str_a, "Hello, world!\n");
  printf("%s", str_a);
}
john@backtrack:~/wonder/2026/jan/14$ gcc -g -o char_array char_array.c 
john@backtrack:~/wonder/2026/jan/14$ ./char_array 
Hello, world!
john@backtrack:~/wonder/2026/jan/14$ gdb ./char_array 
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
Reading symbols from ./char_array...
(gdb) list
1	#include <stdio.h>
2	#include <string.h>
3	
4	int main() {
5	  char str_a[20];
6	
7	  strcpy(str_a, "Hello, world!\n");
8	  printf("%s", str_a);
9	}
(gdb) break 6
Breakpoint 1 at 0x1184: file char_array.c, line 7.
(gdb) break strcpy
Function "strcpy" not defined.
Make breakpoint pending on future shared library load? (y or [n]) y
Breakpoint 2 (strcpy) pending.
(gdb) break 8
Breakpoint 3 at 0x11a3: file char_array.c, line 8.
(gdb) run
Starting program: /home/john/wonder/2026/jan/14/char_array 
Downloading separate debug info for system-supplied DSO at 0x7ffff7fc3000
[Thread debugging using libthread_db enabled]                                                      
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 1, main () at char_array.c:7
7	  strcpy(str_a, "Hello, world!\n");
(gdb) info register rip
rip            0x555555555184      0x555555555184 <main+27>
(gdb) i r rip
rip            0x555555555184      0x555555555184 <main+27>
(gdb) x/5i $rip
=> 0x555555555184 <main+27>:	lea    rax,[rbp-0x20]
   0x555555555188 <main+31>:	movabs rcx,0x77202c6f6c6c6548
   0x555555555192 <main+41>:	mov    QWORD PTR [rax],rcx
   0x555555555195 <main+44>:	movabs rdx,0xa21646c726f77
   0x55555555519f <main+54>:	mov    QWORD PTR [rax+0x7],rdx
(gdb) continue
Continuing.

Breakpoint 3, main () at char_array.c:8
8	  printf("%s", str_a);
(gdb) i r rip
rip            0x5555555551a3      0x5555555551a3 <main+58>
(gdb) x/5i $rip
=> 0x5555555551a3 <main+58>:	lea    rax,[rbp-0x20]
   0x5555555551a7 <main+62>:	mov    rsi,rax
   0x5555555551aa <main+65>:	lea    rax,[rip+0xe53]        # 0x555555556004
   0x5555555551b1 <main+72>:	mov    rdi,rax
   0x5555555551b4 <main+75>:	mov    eax,0x0
(gdb) continue
Continuing.
Hello, world!
[Inferior 1 (process 11177) exited normally]
(gdb) x/5i $rip
No registers.
(gdb) run
Starting program: /home/john/wonder/2026/jan/14/char_array 
Downloading separate debug info for system-supplied DSO at 0x7ffff7fc3000
[Thread debugging using libthread_db enabled]                                                                                                                           
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 1, main () at char_array.c:7
7	  strcpy(str_a, "Hello, world!\n");
(gdb) bt
#0  main () at char_array.c:7
(gdb) cont
Continuing.

Breakpoint 3, main () at char_array.c:8
8	  printf("%s", str_a);
(gdb) bt
#0  main () at char_array.c:8
(gdb) cont
Continuing.
Hello, world!
[Inferior 1 (process 13580) exited normally]
(gdb) quit
```
