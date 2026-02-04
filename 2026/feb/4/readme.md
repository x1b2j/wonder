```
This exploit code is failing on modern Ubuntu systems due to several key security mechanisms that have been implemented. Here's why it doesn't work and what's changed:

## 1. **Stack Canaries**
The error `*** stack smashing detected ***` indicates that the target program (`./notesearch`) was compiled with **stack canary protection**. These are random values placed between buffers and control data on the stack to detect buffer overflows.

## 2. **Non-Executable Stack (NX/DEP)**
Modern systems mark the stack as non-executable by default. Even if you successfully overwrite the return address, the CPU will refuse to execute code from the stack region, causing a segmentation fault.

## 3. **Address Space Layout Randomization (ASLR)**
ASLR randomizes memory addresses (stack, heap, libraries) each time a program runs, making it difficult to predict return addresses like `(unsigned int) &i - offset`.

## 4. **Position Independent Executables (PIE)**
Modern Ubuntu compiles binaries as Position Independent Executables by default, meaning the base address of the executable itself is randomized.

## 5. **64-bit vs 32-bit Architecture**
The shellcode appears to be 32-bit (x86), while modern Ubuntu typically runs 64-bit (x86_64). Even if you compiled the target as 32-bit, other protections still apply.

## What would need to change to make it work:

### If you want to test this for educational purposes:

1. **Disable security features** (not recommended for production):
```bash
# Disable ASLR temporarily
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Compile vulnerable program with no protections
gcc -fno-stack-protector -z execstack -no-pie vulnerable.c -o vulnerable

# Or for 32-bit testing
gcc -m32 -fno-stack-protector -z execstack -no-pie vulnerable.c -o vulnerable
```

2. **Use 64-bit shellcode** if targeting 64-bit systems:
```c
// Example 64-bit shellcode
char shellcode[] = 
    "\x48\x31\xff\x48\x31\xf6\x48\x31\xd2\x48\x31\xc0\x50\x48\xbb"
    "\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x53\x48\x89\xe7\xb0\x3b\x0f\x05";
```

3. **Find correct offsets** using a debugger like GDB with pattern creation tools.

### Modern exploitation techniques:
- **ROP (Return-Oriented Programming)**: Chain existing code snippets (gadgets) to bypass NX
- **Information leaks**: Leak addresses to bypass ASLR
- **Heap exploitation**: Target heap-based vulnerabilities instead of stack
- **Use of one-gadgets**: Find single instructions in libc that spawn shells

### Recommended approach for learning:
1. Use an older VM (Ubuntu 12.04 or earlier)
2. Or use a Docker container with security disabled
3. Or use purpose-built vulnerable VMs like:
   - Metasploitable
   - Damn Vulnerable Linux
   - Protostar/Stack exercises from Exploit Education

This exploit represents "classical" stack-based buffer overflow exploitation that was common in the early 2000s but is largely mitigated by default on modern systems.
```
