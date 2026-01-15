```
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ cat pointer.c 
#include <stdio.h>
#include <string.h>

int main() {
  char str_a[20];
  char *pointer;
  char *pointer2;

  strcpy(str_a, "Hello, world\n");
  pointer = str_a;
  printf(pointer);

  pointer2 = pointer + 2;
  printf(pointer2);
  strcpy(pointer2, "y you guys!\n");
  printf(pointer);
}
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ gcc -o pointer pointer.c 
pointer.c: In function ‘main’:
pointer.c:11:3: warning: format not a string literal and no format arguments [-Wformat-security]
   printf(pointer);
   ^~~~~~
pointer.c:14:3: warning: format not a string literal and no format arguments [-Wformat-security]
   printf(pointer2);
   ^~~~~~
pointer.c:16:3: warning: format not a string literal and no format arguments [-Wformat-security]
   printf(pointer);
   ^~~~~~
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ ./pointer 
Hello, world
llo, world
Hey you guys!
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ gcc -g -o pointer pointer.c 
pointer.c: In function ‘main’:
pointer.c:11:3: warning: format not a string literal and no format arguments [-Wformat-security]
   printf(pointer);
   ^~~~~~
pointer.c:14:3: warning: format not a string literal and no format arguments [-Wformat-security]
   printf(pointer2);
   ^~~~~~
pointer.c:16:3: warning: format not a string literal and no format arguments [-Wformat-security]
   printf(pointer);
   ^~~~~~
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ gdb ./pointer 
GNU gdb (Ubuntu 8.0.1-0ubuntu1) 8.0.1
Copyright (C) 2017 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
<http://www.gnu.org/software/gdb/documentation/>.
For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from ./pointer...done.
(gdb) list
1	#include <stdio.h>
2	#include <string.h>
3	
4	int main() {
5	  char str_a[20];
6	  char *pointer;
7	  char *pointer2;
8	
9	  strcpy(str_a, "Hello, world\n");
10	  pointer = str_a;
(gdb) 
11	  printf(pointer);
12	
13	  pointer2 = pointer + 2;
14	  printf(pointer2);
15	  strcpy(pointer2, "y you guys!\n");
16	  printf(pointer);
17	}
(gdb) 
Line number 18 out of range; pointer.c has 17 lines.
(gdb) break 11
Breakpoint 1 at 0x6e7: file pointer.c, line 11.
(gdb) run
Starting program: /mnt/home/john/wonder/2026/jan/15/pointer 

Breakpoint 1, main () at pointer.c:11
11	  printf(pointer);
(gdb) x/xw pointer
0x7fffffffdc90:	0x6c6c6548
(gdb) x/s pointer
0x7fffffffdc90:	"Hello, world\n"
(gdb) x/xw &pointer
0x7fffffffdc80:	0xffffdc90
(gdb) print &pointer
$1 = (char **) 0x7fffffffdc80
(gdb) print pointer
$2 = 0x7fffffffdc90 "Hello, world\n"
(gdb) quit
A debugging session is active.

	Inferior 1 [process 29993] will be killed.

Quit anyway? (y or n) y
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ vim addressof.c
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ cat addressof.c 
#include <stdio.h>

int main() {
  int int_var = 5;
  int *int_ptr;

  int_ptr = &int_var;
}
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ gcc -g addressof.c 
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ ls
addressof.c  a.out  pointer  pointer.c
john@mrwick:/mnt/home/john/wonder/2026/jan/15$ gdb ./a.out 
GNU gdb (Ubuntu 8.0.1-0ubuntu1) 8.0.1
Copyright (C) 2017 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.  Type "show copying"
and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
<http://www.gnu.org/software/gdb/documentation/>.
For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from ./a.out...done.
(gdb) list
1	#include <stdio.h>
2	
3	int main() {
4	  int int_var = 5;
5	  int *int_ptr;
6	
7	  int_ptr = &int_var;
8	}
(gdb) 
Line number 9 out of range; addressof.c has 8 lines.
(gdb) break 8
Breakpoint 1 at 0x695: file addressof.c, line 8.
(gdb) run
Starting program: /mnt/home/john/wonder/2026/jan/15/a.out 

Breakpoint 1, main () at addressof.c:8
8	}
(gdb) print int_var
$1 = 5
(gdb) print &int_var
$2 = (int *) 0x7fffffffdc9c
(gdb) print int_ptr
$3 = (int *) 0x7fffffffdc9c
(gdb) print &int_ptr
$4 = (int **) 0x7fffffffdca0
(gdb) print *int_ptr
$5 = 5
(gdb) 

```
