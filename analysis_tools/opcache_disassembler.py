#!/usr/bin/env python

# Copyright (c) 2016 GoSecure Inc.

from __future__ import unicode_literals
import opcache_parser
import opcache_parser_64
from treelib import Node, Tree
from termcolor import colored
import re
import sys

class OPcode(Tree):
    """ Tree representation of an OPcode """

    def __init__(self, id, opcode, op_array, context, is_64_bit):
        """ Create a tree representaiton of an Opcode

            Arguments :
                id : The id representing the new OPcode
                opcode : An OPcode struct
                op_array : The op_array of the OPcode
                context : An OPcacheParser instance
        """

        Tree.__init__(self)

        # Identifier to be used by the tree and nodes
        id_with_hash = str(hash(str(op_array))) + "_" + id

        # OP name
        if is_64_bit:
            OPcodeParser = opcache_parser_64.OPcodeParser
        else:
            OPcodeParser = opcache_parser.OPcodeParser

        op = OPcodeParser.get_opcode_name(opcode['opcode'])

        # Parser
        context = OPcodeParser(context)

        # Parse operands and result
        (op1, op2, result) = context.parse_operands(opcode, op_array)

        # Create nodes
        op1_node = Node("Operand 1: " + op1, id_with_hash + "_op1")
        op2_node = Node("Operand 2: " + op2, id_with_hash + "_op2")
        result_node = Node("Result: " + result, id_with_hash + "_result")

        # Link nodes to tree
        self.create_node(id + ": " + op, id_with_hash + "_opcode")
        self.add_node(op1_node, parent=id_with_hash + "_opcode")
        self.add_node(op2_node, parent=id_with_hash + "_opcode")
        self.add_node(result_node, parent=id_with_hash + "_opcode")

class OPcacheDisassembler():

    def __init__(self, is_64_bit, color_output=None):
        self.is_64_bit = is_64_bit
        self.color_output = color_output

    """ Disassembles a given file """


    def _color(self, text, color):
        if self.color_output:
            return colored(text, color)
        else:
            return text


    def syntax_highlight(self, line):
        """ Syntax highlighting for a disassembled Opcache line """

        # JMP
        if "JMP" in line and "->" in line:
            line = re.sub(" (JMP.+)\(", self._color(' \\1', 'green') + "(", line)

        # Variables
        line = re.sub("(\$\d+)", self._color('\\1', 'cyan'), line)

        # Temporary variables
        line = re.sub("(~\d+)", self._color('\\1', 'red'), line)

        # Compiled variables
        line = re.sub("(!\d+)", self._color('\\1', 'yellow'), line)

        # Strings
        line = re.sub("['\"](.+)['\"]", self._color("'\\1'", 'blue'), line)

        return line


    def convert_branch_to_pseudo_code(self, root, nid, indentation = 0):
        """ Convert a branch to readable code

            Arguments :
                root : The root of the AST
                nid : The node ID of the branch to convert, usually 'main_op_array', 'function_table'  or 'class_table'
                indentation : The indentation to use for printing
        """

        line = ""
        lineno = 0
        for child_nid in root[nid].fpointer:

            # Check if the node is an opcode
            if "opcode" in child_nid:
                line += " " * indentation + self.convert_opcode_to_line(root, root[child_nid], lineno) + "\n"
                lineno += 1

            # Else, it's a function/class
            else:
                if "_class_function" in child_nid:
                    prefix = "function "

                elif "_class" in child_nid:
                    prefix = "class "
                else:
                    prefix = "function "

                line += " " * indentation + prefix + root[child_nid].tag + "() {\n"

                indentation += 2
                line += self.convert_branch_to_pseudo_code(root, child_nid, indentation) + "\n"
                indentation -= 2

                line += " " *  indentation + "}\n"

        return line

    def convert_opcode_to_line(self, root, opcode, lineno = 0):
        """ Convert an opcode to a pseudo code using the following syntax : '#1 result = function(param1, param2)'

                Arguments :
                    root : The root of the AST
                    opcode : The OPcode to convert
                    lineno : The line number to use
        """

        # List of children of an OPcode
        children = opcode.fpointer

        # OP name
        op_name = opcode.tag.split(":")[1].strip()

        # Parameters and result
        param1 = root[children[0]].tag.split(":", 1)[1].strip()
        param2 = root[children[1]].tag.split(":", 1)[1].strip()
        result = root[children[2]].tag.split(":", 1)[1].strip()

        # Prepend the line number
        line = "#" + str(lineno) + " "

        # Hide the result part if it's not used
        if result != "None":
            line += result + " = "

        # Final formatting
        line += "{0}({1}, {2});".format(op_name, param1, param2)

        return line

    def create_ast(self, filename):
        """ Create an ast for a given file

            Arguments :
                filename : The name of the file to parse
        """

        # Create parser
        if self.is_64_bit:
            opcache = opcache_parser_64.OPcacheParser(filename)
        else:
            opcache = opcache_parser.OPcacheParser(filename)

        # Create syntax tree
        ast = Tree()
        ast.create_node("script", "script")
        ast.create_node("main_op_array", "main_op_array", parent="script")
        ast.create_node("function_table", "function_table", parent="script")
        ast.create_node("class_table", "class_table", parent="script")

        # Get main structures
        main_op_array = opcache['script']['main_op_array']
        functions = opcache['script']['function_table']['buckets']
        classes = opcache['script']['class_table']['buckets']

        # Main OP array
        for idx, opcode in enumerate(main_op_array['opcodes']):
            opcode = OPcode(str(idx), opcode, main_op_array, opcache, self.is_64_bit)
            ast.paste("main_op_array", opcode)

        # Function Table
        for function in functions:

            # Create function node
            function_name = function['key']['val']
            function_id = function_name + "_function"
            ast.create_node(function_name, function_id, parent="function_table")

            # Iterate over opcodes
            op_array = function['val']['op_array']
            for idx, opcode in enumerate(op_array['opcodes']):
                opcode = OPcode(str(idx), opcode, op_array, opcache, self.is_64_bit)
                ast.paste(function_id, opcode)

        # Class Table
        for class_ in classes:

            # Check for real classes
            if class_['val']['u1']['type'] == IS_PTR:

                # Create class node
                class_name = class_['key']['val']
                class_id = class_name + "_class"
                ast.create_node(class_name, class_id, parent="class_table")

                # Function Table
                for function in class_['val']['class']['function_table']['buckets']:

                    # Create function node
                    function_name = function['key']['val']
                    class_function_id = function_name + "_class_function"
                    ast.create_node(function_name, class_function_id, parent=class_id)

                    # Iterate over opcodes
                    for idx, opcode in enumerate(function['val']['op_array']['opcodes']):
                        opcode = OPcode(str(idx), opcode, function['val']['op_array'], opcache)
                        ast.paste(class_function_id, opcode)


        return ast

    def print_pseudo_code(self, ast):
        """ Print the pseudo code

            Arguments :
                ast : The syntax tree to print
        """

        for line in self.convert_branch_to_pseudo_code(ast, 'class_table', 0).split("\n"):
            print(self.syntax_highlight(line))

        for line in  self.convert_branch_to_pseudo_code(ast, 'function_table', 0).split("\n"):
            print(self.syntax_highlight(line))

        for line in self.convert_branch_to_pseudo_code(ast, 'main_op_array', 0).split("\n"):
            print(self.syntax_highlight(line))

    def print_syntax_tree(self, ast):
        """ Print the syntax tree

            Arguments :
                ast : The syntax tree to print
        """

        ast.show(key=lambda a: "")

    def disassemble(self, file):
        disassembler = OPcacheDisassembler(self.is_64_bit)
        ast = disassembler.create_ast(file)
        final = ""
        final += disassembler.convert_branch_to_pseudo_code(ast, 'class_table', 0)
        final += disassembler.convert_branch_to_pseudo_code(ast, 'function_table', 0)
        final += disassembler.convert_branch_to_pseudo_code(ast, 'main_op_array', 0)

        return final

def show_help():
    """ Show the help menu """

    print("Usage : {0} [-tc] [-a(32|64)] [file]".format(sys.argv[0]))
    print(" " * 4 + "-t Print syntax tree")
    print(" " * 4 + "-c Print pseudocode")
    print(" " * 4 + "-n Disables colored output")
    print(" " * 4 + "-a Architecture (-a32 for 32bit or -a64 for 64bit)")


if __name__ == "__main__":

    show_pseudo_code = False
    show_syntax_tree = False
    is_64_bit = False
    color_output = True

    if len(sys.argv) < 4:
        show_help()
        exit(0)
    else:
        if '-c' in sys.argv:
            show_pseudo_code = True

        if '-t' in sys.argv:
            show_syntax_tree = True

        if '-a32' in sys.argv:
            is_64_bit = False

        if '-a64' in sys.argv:
            is_64_bit = True

        if '-n' in sys.argv:
            color_output = False

    disassembler = OPcacheDisassembler(is_64_bit, color_output)
    ast = disassembler.create_ast(sys.argv[len(sys.argv) - 1])

    if show_syntax_tree:
        disassembler.print_syntax_tree(ast)

    if show_pseudo_code:
        disassembler.print_pseudo_code(ast)
