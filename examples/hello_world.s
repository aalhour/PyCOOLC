.data

# Class name strings
_class_name_Object:
    .word 4
    .word 23
    .word _dispTab_String
    .word 6
    .asciiz "Object"
    .align 2
_class_name_IO:
    .word 4
    .word 19
    .word _dispTab_String
    .word 2
    .asciiz "IO"
    .align 2
_class_name_Int:
    .word 4
    .word 20
    .word _dispTab_String
    .word 3
    .asciiz "Int"
    .align 2
_class_name_Bool:
    .word 4
    .word 21
    .word _dispTab_String
    .word 4
    .asciiz "Bool"
    .align 2
_class_name_String:
    .word 4
    .word 23
    .word _dispTab_String
    .word 6
    .asciiz "String"
    .align 2
_class_name_Main:
    .word 4
    .word 21
    .word _dispTab_String
    .word 4
    .asciiz "Main"
    .align 2
_class_name_table:
    .word _class_name_Object
    .word _class_name_IO
    .word _class_name_Int
    .word _class_name_Bool
    .word _class_name_String
    .word _class_name_Main

# Dispatch tables
_dispTab_Object:
    .word _method_Object_abort
    .word _method_Object_copy
    .word _method_Object_type_name
_dispTab_IO:
    .word _method_Object_abort
    .word _method_Object_copy
    .word _method_Object_type_name
    .word _method_IO_in_int
    .word _method_IO_in_string
    .word _method_IO_out_int
    .word _method_IO_out_string
_dispTab_Int:
    .word _method_Object_abort
    .word _method_Object_copy
    .word _method_Object_type_name
_dispTab_Bool:
    .word _method_Object_abort
    .word _method_Object_copy
    .word _method_Object_type_name
_dispTab_String:
    .word _method_Object_abort
    .word _method_Object_copy
    .word _method_Object_type_name
    .word _method_String_length
    .word _method_String_concat
    .word _method_String_substr
_dispTab_Main:
    .word _method_Object_abort
    .word _method_Object_copy
    .word _method_Object_type_name
    .word _method_IO_in_int
    .word _method_IO_in_string
    .word _method_IO_out_int
    .word _method_IO_out_string
    .word _method_Main_main

# Prototype objects
_protObj_Object:
    .word 0
    .word 12
    .word _dispTab_Object
_protObj_IO:
    .word 1
    .word 12
    .word _dispTab_IO
_protObj_Int:
    .word 2
    .word 16
    .word _dispTab_Int
    .word 0  # _val (void)
_protObj_Bool:
    .word 3
    .word 16
    .word _dispTab_Bool
    .word 0  # _val (void)
_protObj_String:
    .word 4
    .word 20
    .word _dispTab_String
    .word 0  # _val
    .word 0  # _str_field (void)
_protObj_Main:
    .word 5
    .word 12
    .word _dispTab_Main

# String constants
_str_const_empty:
    .word 4
    .word 16
    .word _dispTab_String
    .word 0
    .asciiz ""
    .align 2
_str_const_0:
    .word 4
    .word 20
    .word _dispTab_String
    .word 14
    .asciiz "Hello, World.\n"
    .align 2

# Integer constants

# Boolean constants
_bool_const_false:
    .word 3
    .word 16
    .word _dispTab_Bool
    .word 0
_bool_const_true:
    .word 3
    .word 16
    .word _dispTab_Bool
    .word 1

# Heap management
_heap_start:
    .word 0

.text

# Program entry point
.globl main
main:
    la $t0, _heap_start
    sw $gp, 0($t0)
    la $a0, _protObj_Main
    jal _Object_copy
    jal _init_Main
    jal _method_Main_main
    li $v0, 10
    syscall

# Runtime support routines
_Object_copy:
    lw $t0, 4($a0)
    move $t1, $a0
    move $a0, $t0
    li $v0, 9
    syscall
    move $t2, $v0
    lw $t3, 4($t1)
_Object_copy_loop:
    beqz $t3, _Object_copy_done
    lw $t4, 0($t1)
    sw $t4, 0($t2)
    addiu $t1, $t1, 4
    addiu $t2, $t2, 4
    addiu $t3, $t3, -4
    j _Object_copy_loop
_Object_copy_done:
    move $a0, $v0
    jr $ra

_equality_test:
    beq $a0, $a1, _eq_true
    beqz $a0, _eq_false
    beqz $a1, _eq_false
    lw $t0, 0($a0)
    lw $t1, 0($a1)
    bne $t0, $t1, _eq_false
    li $t2, 2
    bne $t0, $t2, _eq_check_bool
    lw $t0, 12($a0)
    lw $t1, 12($a1)
    beq $t0, $t1, _eq_true
    j _eq_false
_eq_check_bool:
    li $t2, 3
    bne $t0, $t2, _eq_check_string
    lw $t0, 12($a0)
    lw $t1, 12($a1)
    beq $t0, $t1, _eq_true
    j _eq_false
_eq_check_string:
    li $t2, 4
    bne $t0, $t2, _eq_false
    lw $t0, 12($a0)
    lw $t1, 12($a1)
    bne $t0, $t1, _eq_false
    addiu $t2, $a0, 16
    addiu $t3, $a1, 16
_eq_string_loop:
    beqz $t0, _eq_true
    lb $t4, 0($t2)
    lb $t5, 0($t3)
    bne $t4, $t5, _eq_false
    addiu $t2, $t2, 1
    addiu $t3, $t3, 1
    addiu $t0, $t0, -1
    j _eq_string_loop
_eq_true:
    la $a0, _bool_const_true
    jr $ra
_eq_false:
    la $a0, _bool_const_false
    jr $ra

_dispatch_void:
    la $a0, _dispatch_void_msg
    li $v0, 4
    syscall
    li $v0, 10
    syscall
.data
_dispatch_void_msg:
    .asciiz "Error: Dispatch on void\n"
.text


# Built-in methods
_method_Object_abort:
    li $v0, 10
    syscall
_method_Object_type_name:
    lw $t0, 0($a0)
    sll $t0, $t0, 2
    la $t1, _class_name_table
    add $t0, $t0, $t1
    lw $a0, 0($t0)
    jr $ra
_method_Object_copy:
    j _Object_copy
_method_IO_out_string:
    move $t0, $a0
    addiu $a0, $a1, 16
    li $v0, 4
    syscall
    move $a0, $t0
    jr $ra
_method_IO_out_int:
    move $t0, $a0
    lw $a0, 12($a1)
    li $v0, 1
    syscall
    move $a0, $t0
    jr $ra
_method_IO_in_string:
    addiu $sp, $sp, -16
    sw $ra, 12($sp)
    sw $a0, 8($sp)
    li $a0, 1024
    li $v0, 9
    syscall
    sw $v0, 4($sp)
    move $a0, $v0
    li $a1, 1024
    li $v0, 8
    syscall
    lw $t0, 4($sp)
    move $t1, $t0
    li $t2, 0
_in_string_len_loop:
    lb $t3, 0($t1)
    beqz $t3, _in_string_len_done
    li $t4, 10
    beq $t3, $t4, _in_string_len_done
    addiu $t1, $t1, 1
    addiu $t2, $t2, 1
    j _in_string_len_loop
_in_string_len_done:
    sb $zero, 0($t1)
    sw $t2, 0($sp)
    addiu $t2, $t2, 20
    li $t3, -4
    and $a0, $t2, $t3
    li $v0, 9
    syscall
    move $a0, $v0
    li $t0, 4
    sw $t0, 0($a0)
    sw $t2, 4($a0)
    la $t0, _dispTab_String
    sw $t0, 8($a0)
    lw $t0, 0($sp)
    sw $t0, 12($a0)
    lw $t1, 4($sp)
    addiu $t2, $a0, 16
_in_string_copy_loop:
    lb $t3, 0($t1)
    sb $t3, 0($t2)
    beqz $t3, _in_string_copy_done
    addiu $t1, $t1, 1
    addiu $t2, $t2, 1
    j _in_string_copy_loop
_in_string_copy_done:
    lw $ra, 12($sp)
    addiu $sp, $sp, 16
    jr $ra
_method_IO_in_int:
    addiu $sp, $sp, -8
    sw $ra, 4($sp)
    li $v0, 5
    syscall
    sw $v0, 0($sp)
    la $a0, _protObj_Int
    jal _Object_copy
    lw $t0, 0($sp)
    sw $t0, 12($a0)
    lw $ra, 4($sp)
    addiu $sp, $sp, 8
    jr $ra
_method_String_length:
    addiu $sp, $sp, -8
    sw $ra, 4($sp)
    lw $t0, 12($a0)
    sw $t0, 0($sp)
    la $a0, _protObj_Int
    jal _Object_copy
    lw $t0, 0($sp)
    sw $t0, 12($a0)
    lw $ra, 4($sp)
    addiu $sp, $sp, 8
    jr $ra
_method_String_concat:
    jr $ra
_method_String_substr:
    addiu $sp, $sp, -20
    sw $ra, 16($sp)
    sw $a0, 12($sp)
    lw $t0, 12($a1)
    sw $t0, 8($sp)
    lw $t1, 12($a2)
    sw $t1, 4($sp)
    addiu $t2, $t1, 20
    li $t3, -4
    and $a0, $t2, $t3
    sw $a0, 0($sp)
    li $v0, 9
    syscall
    move $a0, $v0
    li $t0, 4
    sw $t0, 0($a0)
    lw $t0, 0($sp)
    sw $t0, 4($a0)
    la $t0, _dispTab_String
    sw $t0, 8($a0)
    lw $t0, 4($sp)
    sw $t0, 12($a0)
    lw $t1, 12($sp)
    addiu $t1, $t1, 16
    lw $t2, 8($sp)
    add $t1, $t1, $t2
    addiu $t2, $a0, 16
    lw $t3, 4($sp)
_substr_copy_loop:
    blez $t3, _substr_copy_done
    lb $t4, 0($t1)
    sb $t4, 0($t2)
    addiu $t1, $t1, 1
    addiu $t2, $t2, 1
    addiu $t3, $t3, -1
    j _substr_copy_loop
_substr_copy_done:
    sb $zero, 0($t2)
    lw $ra, 16($sp)
    addiu $sp, $sp, 20
    jr $ra


# Class initializers
_init_Object:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    lw $a0, 0($fp)
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra

_init_IO:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    lw $a0, 0($fp)
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra

_init_Int:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    lw $a0, 0($fp)
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra

_init_Bool:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    lw $a0, 0($fp)
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra

_init_String:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    lw $a0, 0($fp)
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra

_init_Main:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    jal _init_IO
    lw $a0, 0($fp)
    lw $a0, 0($fp)
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra


# User-defined methods
_method_Main_main:
    addiu $sp, $sp, -12
    sw $fp, 8($sp)
    sw $ra, 4($sp)
    sw $a0, 0($sp)
    move $fp, $sp
    la $a0, _str_const_0
    addiu $sp, $sp, -4
    sw $a0, 0($sp)
    lw $a0, 0($fp)
    beqz $a0, _dispatch_void
    lw $t0, 8($a0)
    lw $t1, 24($t0)
    lw $a1, 0($sp)
    jalr $t1
    addiu $sp, $sp, 4
    lw $ra, 4($fp)
    lw $fp, 8($fp)
    addiu $sp, $sp, 12
    jr $ra
