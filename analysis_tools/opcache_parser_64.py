#!/usr/bin/env python

# Copyright (c) 2016 GoSecure Inc.

from construct import *
from definitions import *

meta = None

def unserialize_zend_function():
    return Zend_Op_Array("op_array")

def unserialize_class():
    return Zend_Class_Entry("class")

def Empty():
    return "Empty" / Struct()

def Z_Val(name, callback = None, unserialize = True):

    if not callback:
        callback = Empty

    callback_name = ""
    if callback == unserialize_zend_function:
        callback_name = "op_array"
    elif callback == unserialize_class:
        callback_name = "class`"

    return name / Struct(Zend_Value("value"),
                  "u1" / Struct("type" / Byte,
                         "type_flags" / Byte,
                         "const_flags" / Byte,
                         "reserved"/ Byte
                  ),
                  "u2" / Int32ul,

                  "string" / If(lambda z: z.u1.type == 6 and unserialize,
                     Pointer(lambda z: (z.value.w1 & ~1) +
                                      (meta['mem_size'] if meta['str_size'] != 0 else 0) +
                                      Meta.sizeof(),
                                      Zend_String("string")
                  )),
                  callback_name / If(lambda z: z.u1.type == 17 and unserialize,
                     Pointer(lambda z: z.value.w1 + Meta.sizeof(), callback()))
                  )

def Pointer_To(name, structure, interned = True):
    structure.name = "value"

    if not interned:
      return name / Struct("position" / Int64ul,
                    structure.name / IfThenElse(lambda z: z.position == 0, Empty(),
                              Pointer(lambda z: (z.position & ~1) +
                                      Meta.sizeof(), structure)
                    ))

    return name / Struct("position" / Int64ul,
                  structure.name / IfThenElse(lambda z: z.position == 0,
                            Empty(),
                            Pointer(lambda z: (z.position & ~1) +
                                    (meta['mem_size'] if meta['str_size'] != 0 else 0) +
                                    Meta.sizeof(), structure)
                  ))

def Zend_Class_Entry(name):
    return name / Struct("padding" / Bytes(3),
                  "type" / Byte,
                  Pointer_To("name", Zend_String("name")),
                  "parent_pos" / Int32ul,
                  "refcount" / Int32ul,
                  "ce_flags" / Int32ul,
                  "default_properties_count" / Int32ul,
                  "default_static_members_count" / Int32ul,
                  "default_properties_table_pos" / Int32ul,
                  "default_static_members_table_pos" / Int32ul,
                  "static_members_table_pos" / Int32ul,
                  Hash_Table("function_table", unserialize_zend_function),
                  Hash_Table("properties_table"),
                  Hash_Table("constants_table"))
                  #Pointer_To("constructor", Zend_Function("constructor"), False))

def Zend_Function(name):
    return name / Struct("type" / Byte,
                  "arg_flags" / Bytes(3),
                  ULInt32("fn_flags"),
                  Pointer_To("function_name", Zend_String("function_name")),
                  ULInt32("scope_pos"),
                  ULInt32("prototype_pos"),
                  ULInt32("num_args"),
                  ULInt32("required_num_args"),
                  Pointer_To("arg_info", Zend_String("arg_info"), False))

def Bucket(name, callback = None):
    return name / Struct(Z_Val("val", callback),
                  "h" / Int64ul,
                  "key_pos" / Int64ul,
                  "key" / If(this.val.u1.type != 0,
                     Pointer(lambda z: (z.key_pos & ~1) +
                             (meta['mem_size'] if meta['str_size'] != 0 else 0) +
                             Meta.sizeof(), Zend_String("key"))
                  ))

def Hash_Table(name, callback = None):
    return name / Struct(Zend_Refcounted_H("gc"),
                  "flags" / Int32ul,
                  "nTableMask" / Int32ul,
                  "bucket_pos" / Int64ul,
                  "nNumUsed" / Int32ul,
                  "nNumOfElements" / Int32ul,
                  "nTableSize" / Int32ul,
                  "nInternalPointer" / Int32ul,
                  "nNextFreeElement" / Int64ul,
                  "pDestructor" / Int64ul,
                  Pointer(lambda z: z.bucket_pos + Meta.sizeof(),
                    Array(lambda z: z.nNumUsed,
                      Bucket("buckets", callback)
                  ))
                  )

def Zend_Value(name):
    return name / Struct("w1" / Int32ul,
                  "w2" / Int32ul)


def Zend_Refcounted_H(name):
    return  name / Struct("refcount" / Int32ul,
                   "typeinfo" / Int32ul)


def Zend_String(name):
    return name / Struct(Zend_Refcounted_H("gc"),
                  "h" / Int64ul,
                  "len" / Int64ul,
                  "val" / Bytes(this.len))

def Zend_Arg_Info(name):
    return name / Struct(Pointer_To("name", Zend_String("name")),
                  Pointer_To("class_name", Zend_String("class_name")),
                  "class_name_pos" / Int32ul,
                  "type_hint" / Byte,
                  "pass_by_reference" / Byte,
                  "allow_null" / Byte,
                  "is_variadic" / Byte)

def Z_Node_Op(name):
    return name / Struct("val" / Int32ul)

def Zend_Op(name):
    return name / Struct("handler" / Int64ul,
                  Z_Node_Op("op1"),
                  Z_Node_Op("op2"),
                  Z_Node_Op("result"),
                  "extended_value" / Int32ul,
                  "lineno" / Int32ul,
                  "opcode" / Byte,
                  "op1_type" / Byte,
                  "op2_type" / Byte,
                  "result_type" / Byte)

def Zend_Op_Array(name):
    return name / Struct("type" / Byte,
                    "arg_flags" /  Bytes(3),
                    "fn_flags" / Int32ul,
                    Pointer_To("function_name", Zend_String("function_name")),
                    "scope_pos" / Int64ul,
                    Pointer_To("prototype", Zend_String("prototype")),
                    "num_args" / Int32ul,
                    "required_num_args" / Int32ul,
                    Pointer_To("arg_info", Zend_Arg_Info("arg_info"), False),
                    "refcount" / Int64ul,
                    "this_var" / Int32ul,
                    "last" / Int32ul,
                    "opcodes_pos" / Int64ul,
                    Pointer(lambda z: z.opcodes_pos + Meta.sizeof(),
                            Array(lambda z: z.last,
                                  Zend_Op("opcodes")
                            )
                    ),
                    "last_var" / Int32ul,
                    "T" / Int32ul,
                    "vars_pos_pos" / Int64ul,
                    Pointer(lambda z: z.vars_pos_pos + Meta.sizeof(),
                            Array(lambda z: z.last_var,
                                "vars" / Struct("pos" / Int64ul,
                                       Pointer(lambda v: (v.pos & ~1) +
                                       (meta['mem_size'] if meta['str_size'] != 0 else 0) +
                                       Meta.sizeof(), Zend_String("var")))
                            )
                    ),
                    "last_live_range" / Int32ul,
                    "last_try_catch" / Int32ul,
                    "live_range_pos" / Int64ul,
                    "try_catch_array_pos" / Int64ul,
                    Pointer_To("static_variables", Hash_Table("static_variables"), False),
                    Pointer_To("filename", Zend_String("filename"), False),
                    "line_start" / Int32ul,
                    "line_end" / Int32ul,
                    Pointer_To("doc_comment", Zend_String("doc_comment"), False),
                    "early_binding" / Int32ul,
                    "last_literals" / Int32ul,
                    "literals_pos" / Int64ul,
                    Pointer(lambda z: z.literals_pos + Meta.sizeof(),
                            Array(lambda z: z.last_literals,
                                  Z_Val("literals")
                            )
                    ),
                    "cache_size" / Int64ul,
                    "runtime_size" / Int64ul,
                    Array(4, "reserved" / Int64ul))

Script = "script" / Struct(Pointer_To("filename", Zend_String("filename"), False),
                Zend_Op_Array("main_op_array"),
                Hash_Table("function_table", unserialize_zend_function),
                Hash_Table("class_table", unserialize_class))

Meta = "meta" / Struct("magic" / Bytes(8),
              "system_id" / Bytes(32),
              "mem_size" / Int64ul,
              "str_size" / Int64ul,
              "script_offset" / Int64ul,
              "timestamp" / Int64ul,
              "checksum" / Int64ul)

OPcache = "OPcache" / Struct(Meta,
                             Script)

class OPcodeParser():
    """ Parser for everything related to opcodes """

    @staticmethod
    def get_opcode_name(opcode):
        """ Get the name for a given op number """

        return OPCODES[opcode]

    def __init__(self, opcache):
        """ Keep track of the file stream for parsing

            Arguments :
                opcache : An OPcache instance to be used as context
        """

        self.stream = opcache.stream

    def parse_jmp(self, opcode, op_array):
        """ Parse jump instructions

            Arguments :
                opcode : An opcode struct
                op_array : The op array of the opcode
        """

        zend_op_size = Zend_Op("").sizeof()
        op1_val = opcode['op1']['val']
        op2_val = opcode['op2']['val']
        opcodes_pos = op_array['opcodes_pos']

        # Unconditional jump (no second operand)
        if opcode['opcode'] == 42:
            op1 = "->" + str((op1_val - opcodes_pos) / zend_op_size)
            op2 = "None"

        # Other jump instructions
        else:
            op1 = self.parse_zval(op2_val, opcode['op1_type'], op_array)
            op2 = "->" + str((op2_val - opcodes_pos) / zend_op_size)

        return (op1, op2, "None")

    def parse_operands(self, opcode, op_array):
        """ Parse the two operands and the result

            Arguments :
                opcode : An opcode struct
                op_array : The op array of the opcode
        """

        # OP number and name
        op_no = opcode['opcode']

        # Treat jump instructions differently
        if 42 <= op_no and op_no <= 47:
            (op1, op2, result) = self.parse_jmp(opcode, op_array)

        else:
            op1 = self.parse_zval(opcode['op1'].val, opcode['op1_type'], op_array)
            op2 = self.parse_zval(opcode['op2'].val, opcode['op2_type'], op_array)
            result = self.parse_zval(opcode['result'].val, opcode['result_type'], op_array)

        return (op1, op2, result)

    def parse_zval(self, offset, op_type, op_array):
        """ Parse a zval at a offset for a given operand type

            Arguments :
                offset : The offset of the zval
                op_type : The type of the operand
        """

        # Size to add to the offset
        size_of_meta = Meta.sizeof()

        # If the offset is invalid, consider the operand as unused

        try:
            #zval = Z_Val("val", unserialize=False).parse(self.stream[offset:])
            zval = op_array["literals"][offset / 16]

        except:
            return "None"

        # Get the type of the z_val and the two possible values
        type = zval['u1']['type']
        w1 = zval['value']['w1']
        w2 = zval['value']['w2']

        # Interpret the z_val
        if op_type == IS_CONST:
            if type == IS_STRING:
                return repr(Zend_String("val").parse(self.stream[(w1 & ~1) + (meta['mem_size'] if meta['str_size'] != 0 else 0) + size_of_meta:])['val'])

            if type == IS_LONG:
                return str(w1)

            if type == IS_NULL:
                return "None"

        if op_type == IS_TMP_VAR:
            return "~" + str(w2)

        if op_type == IS_VAR:
            return "$" + str(w2)

        if op_type == IS_UNUSED:
            return "None"

        if op_type == IS_CV:
            return "!" + str(w2)

        return "None"



class OPcacheParser():
    """ Parses a given OPcache file """

    def __init__(self, file_path):
        """ Parses a given OPcache file
            Arguments :
                file_path : The path of the file to parse
        """

        with open(file_path, "rb") as file:
            self.stream = file.read()

        self.parsed = OPcacheParser.parse_stream(self.stream)

    def __getitem__(self, index):
        return self.parsed[index]

    @staticmethod
    def parse_stream(stream):
        global meta
        meta = Meta.parse(stream)
        return OPcache.parse(stream)
