```
#. Experimenting with void pointers quickly reveals a few things about 
typeless pointers. First, pointers can not be de-referenced unless they
have a type. In order to retrieve the value stored in the pointer's 
memory address, the compiler must first know what type of data it is.
Secondly, void pointers must also be typecast before doing pointer 
arithmatic. These are fairly intuitive limitations, which means that a
void pointer's main purpose is to simply hold a memory address.

#. When the program isn't given enough command-line arguments, it still
tries to access elements of the argument array, even though they don't
exist. This results in the program crashing due to a segmentation 
fault.  Memory is split into segments (which will be discussed later),
and some memory addresses aren't within the boundaries of the memory 
segments the program is given access to. When the program attempts to 
access an address that is out of bounds, it will crash and die in 
what's called a segmentation fault. This effect can be explored further
with GDB.
```
