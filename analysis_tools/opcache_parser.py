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
    return Struct("Empty")

def Z_Val(name, callback = None, unserialize = True):

    if not callback:
        callback = Empty

    return Struct(name,
                  Zend_Value("value"),
                  Struct("u1",
                         Byte("type"),
                         Byte("type_flags"),
                         Byte("const_flags"),
                         Byte("reserved")
                  ),
                  ULInt32("u2"),

                  If(lambda z: z.u1.type == 6 and unserialize,
                     OnDemand(Pointer(lambda z: (z.value.w1 & ~1) +
                                      (meta['mem_size'] if meta['str_size'] != 0 else 0) +
                                      Struct.sizeof(Meta),
                                      Zend_String("string"))
                  )),
                  If(lambda z: z.u1.type == 17 and unserialize,
                     Pointer(lambda z: z.value.w1 + Struct.sizeof(Meta), callback()))
                  )

def Pointer_To(name, structure):
    structure.name = "value"
    return Struct(name,
                  ULInt32("position"),
                  IfThenElse(structure.name, lambda z: z.position == 0,
                            Empty(),
                            Pointer(lambda z: (z.position & ~1) + Struct.sizeof(Meta), structure))
                  )

def Zend_Class_Entry(name):
    return Struct(name,
                  Bytes("padding", 3),
                  Byte("type"),
                  Pointer_To("name", Zend_String("name")),
                  ULInt32("parent_pos"),
                  ULInt32("refcount"),
                  ULInt32("ce_flags"),
                  ULInt32("default_properties_count"),
                  ULInt32("default_static_members_count"),
                  ULInt32("default_properties_table_pos"),
                  ULInt32("default_static_members_table_pos"),
                  ULInt32("static_members_table_pos"),
                  Hash_Table("function_table", unserialize_zend_function),
                  Hash_Table("properties_table"),
                  Hash_Table("constants_table"),
                  Pointer_To("constructor", Zend_Function("constructor")))

def Zend_Function(name):
    return Struct(name,
                  Byte("type"),
                  Bytes("arg_flags", 3),
                  ULInt32("fn_flags"),
                  Pointer_To("function_name", Zend_String("function_name")),
                  ULInt32("scope_pos"),
                  ULInt32("prototype_pos"),
                  ULInt32("num_args"),
                  ULInt32("required_num_args"),
                  Pointer_To("arg_info", Zend_String("arg_info")))

def Bucket(name, callback = None):
    return Struct(name,
                  Z_Val("val", callback),
                  ULInt32("h"),
                  ULInt32("key_pos"),
                  If(lambda z: z.val.u1.type != 0,
                     Pointer(lambda z: z.key_pos + Struct.sizeof(Meta), Zend_String("key")))
                  )

def Hash_Table(name, callback = None):
    return Struct(name,
                  Zend_Refcounted_H("gc"),
                  ULInt32("flags"),
                  ULInt32("nTableMask"),
                  ULInt32("bucket_pos"),
                  ULInt32("nNumUsed"),
                  ULInt32("nNumOfElements"),
                  ULInt32("nTableSize"),
                  ULInt32("nInternalPointer"),
                  ULInt32("nNextFreeElement"),
                  ULInt32("pDestructor"),
                  Pointer(lambda z: z.bucket_pos + Struct.sizeof(Meta),
                    Array(lambda z: z.nNumUsed,
                      Bucket("buckets", callback)
                  ))
                  )

def Zend_Value(name):
    return Struct(name,
                  ULInt32("w1"),
                  ULInt32("w2"))


def Zend_Refcounted_H(name):
    return  Struct(name,
                   ULInt32("refcount"),
                   ULInt32("typeinfo"))


def Zend_String(name):
    return Struct(name,
                  Zend_Refcounted_H("gc"),
                  ULInt32("h"),
                  ULInt32("len"),
                  String("val", lambda zs: zs.len))

def Zend_Arg_Info(name):
    return Struct(name,
                  Pointer_To("name", Zend_String("name")),
                  Pointer_To("class_name", Zend_String("class_name")),
                  Byte("type_hint"),
                  Byte("pass_by_reference"),
                  Byte("allow_null"),
                  Byte("is_variadic"))

def Z_Node_Op(name):
    return Struct(name,
                  ULInt32("val"))

def Zend_Op(name):
    return Struct(name,
                  ULInt32("handler"),
                  Z_Node_Op("op1"),
                  Z_Node_Op("op2"),
                  Z_Node_Op("result"),
                  ULInt32("extended_value"),
                  ULInt32("lineno"),
                  Byte("opcode"),
                  Byte("op1_type"),
                  Byte("op2_type"),
                  Byte("result_type"))

def Zend_Op_Array(name):
    return Struct(name,
                    Byte("type"),
                    Bytes("arg_flags", 3),
                    ULInt32("fn_flags"),
                    Pointer_To("function_name", Zend_String("function_name")),
                    ULInt32("scope_pos"),
                    Pointer_To("prototype", Zend_String("prototype")),
                    ULInt32("num_args"),
                    ULInt32("required_num_args"),
                    Pointer_To("arg_info", Zend_Arg_Info("arg_info")),
                    ULInt32("refcount"),
                    ULInt32("this_var"),
                    ULInt32("last"),
                    ULInt32("opcodes_pos"),
                    Pointer(lambda z: z.opcodes_pos + Struct.sizeof(Meta),
                            Array(lambda z: z.last,
                                  Zend_Op("opcodes")
                            )
                    ),
                    ULInt32("last_var"),
                    ULInt32("T"),
                    ULInt32("vars_pos_pos"),
                    Pointer(lambda z: z.vars_pos_pos + Struct.sizeof(Meta),
                            Array(lambda z: z.last_var,
                                Struct("vars",
                                       ULInt32("pos"))
                                       #Pointer(lambda v: v.pos + Struct.sizeof(Meta), Zend_String("var")))
                            )
                    ),
                    ULInt32("last_live_range"),
                    ULInt32("last_try_catch"),
                    ULInt32("live_range_pos"),
                    ULInt32("try_catch_array_pos"),
                    Pointer_To("static_variables", Hash_Table("static_variables")),
                    Pointer_To("filename", Zend_String("filename")),
                    ULInt32("line_start"),
                    ULInt32("line_end"),
                    Pointer_To("doc_comment", Zend_String("doc_comment")),
                    ULInt32("early_binding"),
                    ULInt32("last_literals"),
                    ULInt32("literals_pos"),
                    Pointer(lambda z: z.literals_pos + Struct.sizeof(Meta),
                            Array(lambda z: z.last_literals,
                                  Z_Val("literals")
                            )
                    ),
                    ULInt32("cache_size"),
                    ULInt32("runtime_size"),
                    Array(4, ULInt32("reserved")))

Script = Struct("script",
                Pointer_To("filename", Zend_String("filename")),
                Zend_Op_Array("main_op_array"),
                Hash_Table("function_table", unserialize_zend_function),
                Hash_Table("class_table", unserialize_class))

Meta = Struct("meta",
              String("magic", 8),
              String("system_id", 32),
              ULInt32("mem_size"),
              ULInt32("str_size"),
              ULInt32("script_offset"),
              ULInt32("timestamp"),
              ULInt32("checksum"))

OPcache = Struct("OPcache",
                 Meta,
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

        zend_op_size = Struct.sizeof(Zend_Op(""))
        op1_val = opcode['op1']['val']
        op2_val = opcode['op2']['val']
        opcodes_pos = op_array['opcodes_pos']

        # Unconditional jump (no second operand)
        if opcode['opcode'] == 42:
            op1 = "->" + str((op1_val - opcodes_pos) / zend_op_size)
            op2 = "None"

        # Other jump instructions
        else:
            op1 = self.parse_zval(op2_val, opcode['op1_type'])
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
            op1 = self.parse_zval(opcode['op1'].val, opcode['op1_type'])
            op2 = self.parse_zval(opcode['op2'].val, opcode['op2_type'])
            result = self.parse_zval(opcode['result'].val, opcode['result_type'])

        return (op1, op2, result)

    def parse_zval(self, offset, op_type):
        """ Parse a zval at a offset for a given operand type

            Arguments :
                offset : The offset of the zval
                op_type : The type of the operand
        """

        # Size to add to the offset
        size_of_meta = Struct.sizeof(Meta)

        # If the offset is invalid, consider the operand as unused
        try:
            zval = Z_Val("val", unserialize=False).parse(self.stream[offset + size_of_meta:])
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

        with open(file_path, "r") as file:
            self.stream = file.read()

        self.parsed = OPcacheParser.parse_stream(self.stream)

        global meta
        meta = self.parsed['meta']

    def __getitem__(self, index):
        return self.parsed[index]

    @staticmethod
    def parse_stream(stream):

        return OPcache.parse(stream)
