import re
from typing import List, Optional, Union
from dataclasses import dataclass

# AST Knoten-Definitionen
@dataclass
class ASTNode:
    """Basis-Klasse für alle AST-Knoten"""
    pass

@dataclass
class Program(ASTNode):
    declarations: List[ASTNode]

@dataclass
class FunctionDecl(ASTNode):
    return_type: str
    name: str
    params: List['VarDecl']
    body: 'CompoundStmt'

@dataclass
class VarDecl(ASTNode):
    var_type: str
    name: str
    init_value: Optional[ASTNode] = None

@dataclass
class CompoundStmt(ASTNode):
    statements: List[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_stmt: ASTNode
    else_stmt: Optional[ASTNode] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: ASTNode

@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode

@dataclass
class Assignment(ASTNode):
    target: str
    value: ASTNode

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class Literal(ASTNode):
    value: Union[int, float, str]
    lit_type: str  # 'int', 'float', 'string'

@dataclass
class ArrayDecl(ASTNode):
    element_type: str
    name: str
    size: Optional[ASTNode]
    init_values: Optional[List[ASTNode]] = None

@dataclass
class ArrayAccess(ASTNode):
    array_name: str
    index: ASTNode

@dataclass
class StructDecl(ASTNode):
    name: str
    members: List[VarDecl]

@dataclass
class StructVarDecl(ASTNode):
    struct_name: str
    var_name: str
    init_value: Optional[ASTNode] = None

@dataclass
class MemberAccess(ASTNode):
    object: ASTNode
    member: str

@dataclass
class ForStmt(ASTNode):
    init: Optional[ASTNode]
    condition: Optional[ASTNode]
    increment: Optional[ASTNode]
    body: ASTNode

# Lexer (Tokenizer)
class Token:
    def __init__(self, type_, value, line=0):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    TOKEN_PATTERNS = [
        ('COMMENT_MULTI', r'/\*.*?\*/'),
        ('COMMENT_SINGLE', r'//.*'),
        ('NUMBER', r'\d+\.?\d*'),
        ('STRING', r'"[^"]*"'),
        ('KEYWORD', r'\b(int|float|void|return|if|else|while|for|struct)\b'),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('SEMICOLON', r';'),
        ('COMMA', r','),
        ('DOT', r'\.'),
        ('ASSIGN', r'='),
        ('PLUS', r'\+'),
        ('MINUS', r'-'),
        ('MULT', r'\*'),
        ('DIV', r'/'),
        ('LE', r'<='),
        ('GE', r'>='),
        ('EQ', r'=='),
        ('NE', r'!='),
        ('LT', r'<'),
        ('GT', r'>'),
        ('WHITESPACE', r'\s+'),
    ]

    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []
        self.tokenize()

    def tokenize(self):
        line = 1
        while self.pos < len(self.code):
            matched = False
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)
                if match:
                    value = match.group(0)
                    if token_type not in ('WHITESPACE', 'COMMENT_SINGLE', 'COMMENT_MULTI'):
                        self.tokens.append(Token(token_type, value, line))
                    line += value.count('\n')
                    self.pos = match.end()
                    matched = True
                    break
            if not matched:
                raise SyntaxError(f"Unbekanntes Zeichen: '{self.code[self.pos]}' in Zeile {line}")

# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type=None):
        token = self.current_token()
        if token is None:
            raise SyntaxError("Unerwartetes Ende der Eingabe")
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"Erwartet {expected_type}, erhalten {token.type} ('{token.value}') in Zeile {token.line}")
        self.pos += 1
        return token

    def match(self, *types):
        token = self.current_token()
        return token and token.type in types

    def parse(self):
        """Haupt-Parsing-Methode"""
        declarations = []
        while self.current_token():
            declarations.append(self.parse_declaration())
        return Program(declarations)

    def parse_declaration(self):
        """Parsing von Funktions-, Variablen-, Array- oder Struct-Deklarationen"""
        token = self.current_token()

        # Struct-Deklaration
        if token and token.type == 'KEYWORD' and token.value == 'struct':
            return self.parse_struct_declaration()

        # Normale Deklarationen
        if token and token.type == 'KEYWORD':
            type_token = self.consume('KEYWORD')
            name_token = self.consume('IDENTIFIER')

            if self.match('LPAREN'):
                return self.parse_function(type_token.value, name_token.value)
            elif self.match('LBRACKET'):
                return self.parse_array_declaration(type_token.value, name_token.value)
            else:
                return self.parse_variable(type_token.value, name_token.value)

        raise SyntaxError(f"Unerwartetes Token bei Deklaration: {token}")

    def parse_function(self, return_type, name):
        """Parsing einer Funktionsdeklaration"""
        self.consume('LPAREN')
        params = []

        if not self.match('RPAREN'):
            params.append(self.parse_parameter())
            while self.match('COMMA'):
                self.consume('COMMA')
                params.append(self.parse_parameter())

        self.consume('RPAREN')
        body = self.parse_compound_stmt()
        return FunctionDecl(return_type, name, params, body)

    def parse_parameter(self):
        """Parsing eines Funktionsparameters"""
        var_type = self.consume('KEYWORD').value
        var_name = self.consume('IDENTIFIER').value

        # Array-Parameter (z.B. int arr[])
        if self.match('LBRACKET'):
            self.consume('LBRACKET')
            # Optional: Array-Größe (meist leer bei Parametern)
            if not self.match('RBRACKET'):
                size = self.parse_expression()
            self.consume('RBRACKET')
            var_type = var_type + "[]"

        return VarDecl(var_type, var_name)

    def parse_variable(self, var_type, var_name):
        """Parsing einer Variablendeklaration"""
        init_value = None
        if self.match('ASSIGN'):
            self.consume('ASSIGN')
            init_value = self.parse_expression()
        self.consume('SEMICOLON')
        return VarDecl(var_type, var_name, init_value)

    def parse_array_declaration(self, element_type, array_name):
        """Parsing einer Array-Deklaration"""
        self.consume('LBRACKET')
        size = None
        if not self.match('RBRACKET'):
            size = self.parse_expression()
        self.consume('RBRACKET')

        init_values = None
        if self.match('ASSIGN'):
            self.consume('ASSIGN')
            self.consume('LBRACE')
            init_values = []
            if not self.match('RBRACE'):
                init_values.append(self.parse_expression())
                while self.match('COMMA'):
                    self.consume('COMMA')
                    if self.match('RBRACE'):  # Trailing comma
                        break
                    init_values.append(self.parse_expression())
            self.consume('RBRACE')

        self.consume('SEMICOLON')
        return ArrayDecl(element_type, array_name, size, init_values)

    def parse_struct_declaration(self):
        """Parsing einer Struct-Deklaration"""
        self.consume('KEYWORD')  # 'struct'
        struct_name = self.consume('IDENTIFIER').value

        # Struct-Definition mit Members
        if self.match('LBRACE'):
            self.consume('LBRACE')
            members = []
            while not self.match('RBRACE'):
                member_type = self.consume('KEYWORD').value
                member_name = self.consume('IDENTIFIER').value

                # Array-Member
                if self.match('LBRACKET'):
                    self.consume('LBRACKET')
                    size = None
                    if not self.match('RBRACKET'):
                        size = self.parse_expression()
                    self.consume('RBRACKET')
                    members.append(VarDecl(f"{member_type}[]", member_name))
                else:
                    members.append(VarDecl(member_type, member_name))

                self.consume('SEMICOLON')

            self.consume('RBRACE')
            self.consume('SEMICOLON')
            return StructDecl(struct_name, members)

        # Struct-Variable-Deklaration
        else:
            var_name = self.consume('IDENTIFIER').value
            init_value = None
            if self.match('ASSIGN'):
                self.consume('ASSIGN')
                init_value = self.parse_expression()
            self.consume('SEMICOLON')
            return StructVarDecl(struct_name, var_name, init_value)

    def parse_compound_stmt(self):
        """Parsing eines Block-Statements { ... }"""
        self.consume('LBRACE')
        statements = []
        while not self.match('RBRACE'):
            statements.append(self.parse_statement())
        self.consume('RBRACE')
        return CompoundStmt(statements)

    def parse_statement(self):
        """Parsing verschiedener Statement-Typen"""
        token = self.current_token()

        if not token:
            raise SyntaxError("Unerwartetes Ende in Statement")

        if token.type == 'KEYWORD':
            if token.value == 'return':
                return self.parse_return_stmt()
            elif token.value == 'if':
                return self.parse_if_stmt()
            elif token.value == 'while':
                return self.parse_while_stmt()
            elif token.value == 'for':
                return self.parse_for_stmt()
            elif token.value == 'struct':
                return self.parse_struct_declaration()
            elif token.value in ('int', 'float', 'void'):
                type_val = self.consume('KEYWORD').value
                name_val = self.consume('IDENTIFIER').value
                if self.match('LBRACKET'):
                    return self.parse_array_declaration(type_val, name_val)
                else:
                    return self.parse_variable(type_val, name_val)

        if self.match('LBRACE'):
            return self.parse_compound_stmt()

        if self.match('IDENTIFIER'):
            name = self.current_token().value
            self.consume('IDENTIFIER')

            # Array-Zuweisung
            if self.match('LBRACKET'):
                self.consume('LBRACKET')
                index = self.parse_expression()
                self.consume('RBRACKET')

                # Member-Zugriff auf Array-Element
                if self.match('DOT'):
                    array_access = ArrayAccess(name, index)
                    self.consume('DOT')
                    member = self.consume('IDENTIFIER').value
                    member_access = MemberAccess(array_access, member)
                    self.consume('ASSIGN')
                    value = self.parse_expression()
                    self.consume('SEMICOLON')
                    return Assignment(f"{name}[index].{member}", value)
                else:
                    self.consume('ASSIGN')
                    value = self.parse_expression()
                    self.consume('SEMICOLON')
                    return Assignment(f"{name}[index]", value)

            # Member-Zugriff und Zuweisung (z.B. p.x = 10)
            if self.match('DOT'):
                members = [name]
                while self.match('DOT'):
                    self.consume('DOT')
                    members.append(self.consume('IDENTIFIER').value)

                self.consume('ASSIGN')
                value = self.parse_expression()
                self.consume('SEMICOLON')
                member_path = '.'.join(members)
                return Assignment(member_path, value)

            # Normale Zuweisung
            if self.match('ASSIGN'):
                self.consume('ASSIGN')
                value = self.parse_expression()
                self.consume('SEMICOLON')
                return Assignment(name, value)

            # Funktionsaufruf oder Ausdruck
            elif self.match('LPAREN'):
                self.pos -= 1
                expr = self.parse_expression()
                self.consume('SEMICOLON')
                return expr

        raise SyntaxError(f"Unerwartetes Token: {token}")

    def parse_return_stmt(self):
        """Parsing eines Return-Statements"""
        self.consume('KEYWORD')
        value = None
        if not self.match('SEMICOLON'):
            value = self.parse_expression()
        self.consume('SEMICOLON')
        return ReturnStmt(value)

    def parse_if_stmt(self):
        """Parsing eines If-Statements"""
        self.consume('KEYWORD')
        self.consume('LPAREN')
        condition = self.parse_expression()
        self.consume('RPAREN')
        then_stmt = self.parse_statement()
        else_stmt = None
        if self.match('KEYWORD') and self.current_token().value == 'else':
            self.consume('KEYWORD')
            else_stmt = self.parse_statement()
        return IfStmt(condition, then_stmt, else_stmt)

    def parse_while_stmt(self):
        """Parsing eines While-Statements"""
        self.consume('KEYWORD')
        self.consume('LPAREN')
        condition = self.parse_expression()
        self.consume('RPAREN')
        body = self.parse_statement()
        return WhileStmt(condition, body)

    def parse_for_stmt(self):
        """Parsing eines For-Statements"""
        self.consume('KEYWORD')  # 'for'
        self.consume('LPAREN')

        # Init (kann Deklaration oder Ausdruck sein)
        init = None
        if not self.match('SEMICOLON'):
            if self.match('KEYWORD'):
                type_val = self.consume('KEYWORD').value
                name_val = self.consume('IDENTIFIER').value
                init_value = None
                if self.match('ASSIGN'):
                    self.consume('ASSIGN')
                    init_value = self.parse_expression()
                init = VarDecl(type_val, name_val, init_value)
            else:
                # Zuweisung als Init
                name = self.consume('IDENTIFIER').value
                self.consume('ASSIGN')
                value = self.parse_expression()
                init = Assignment(name, value)
        self.consume('SEMICOLON')

        # Condition
        condition = None
        if not self.match('SEMICOLON'):
            condition = self.parse_expression()
        self.consume('SEMICOLON')

        # Increment
        increment = None
        if not self.match('RPAREN'):
            name = self.consume('IDENTIFIER').value
            if self.match('ASSIGN'):
                self.consume('ASSIGN')
                value = self.parse_expression()
                increment = Assignment(name, value)
            else:
                # Für i++ oder i-- würde man hier weitere Logik brauchen
                self.pos -= 1
                increment = self.parse_expression()

        self.consume('RPAREN')
        body = self.parse_statement()
        return ForStmt(init, condition, increment, body)

    def parse_expression(self):
        """Parsing von Ausdrücken (vereinfacht)"""
        return self.parse_comparison()

    def parse_comparison(self):
        """Parsing von Vergleichsoperationen"""
        left = self.parse_additive()
        while self.match('LT', 'GT', 'LE', 'GE', 'EQ', 'NE'):
            op = self.consume().value
            right = self.parse_additive()
            left = BinaryOp(op, left, right)
        return left

    def parse_additive(self):
        """Parsing von Addition/Subtraktion"""
        left = self.parse_multiplicative()
        while self.match('PLUS', 'MINUS'):
            op = self.consume().value
            right = self.parse_multiplicative()
            left = BinaryOp(op, left, right)
        return left

    def parse_multiplicative(self):
        """Parsing von Multiplikation/Division"""
        left = self.parse_unary()
        while self.match('MULT', 'DIV'):
            op = self.consume().value
            right = self.parse_unary()
            left = BinaryOp(op, left, right)
        return left

    def parse_unary(self):
        """Parsing von Unären Operationen"""
        if self.match('MINUS'):
            op = self.consume().value
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        return self.parse_primary()

    def parse_primary(self):
        """Parsing von primären Ausdrücken"""
        token = self.current_token()

        if token.type == 'NUMBER':
            self.consume()
            value = float(token.value) if '.' in token.value else int(token.value)
            lit_type = 'float' if '.' in token.value else 'int'
            return Literal(value, lit_type)

        if token.type == 'STRING':
            self.consume()
            return Literal(token.value[1:-1], 'string')

        if token.type == 'IDENTIFIER':
            name = token.value
            self.consume()

            # Array-Zugriff
            if self.match('LBRACKET'):
                self.consume('LBRACKET')
                index = self.parse_expression()
                self.consume('RBRACKET')
                result = ArrayAccess(name, index)
                # Member-Zugriff auf Array-Element
                while self.match('DOT'):
                    self.consume('DOT')
                    member = self.consume('IDENTIFIER').value
                    result = MemberAccess(result, member)
                return result

            # Member-Zugriff
            if self.match('DOT'):
                result = Identifier(name)
                while self.match('DOT'):
                    self.consume('DOT')
                    member = self.consume('IDENTIFIER').value
                    result = MemberAccess(result, member)
                return result

            # Funktionsaufruf
            if self.match('LPAREN'):
                self.consume('LPAREN')
                args = []
                if not self.match('RPAREN'):
                    args.append(self.parse_expression())
                    while self.match('COMMA'):
                        self.consume('COMMA')
                        args.append(self.parse_expression())
                self.consume('RPAREN')
                return FunctionCall(name, args)

            return Identifier(name)

        if self.match('LPAREN'):
            self.consume('LPAREN')
            expr = self.parse_expression()
            self.consume('RPAREN')
            return expr

        raise SyntaxError(f"Unerwartetes Token: {token}")

# Hilfsfunktion zum Ausgeben des AST
def print_ast(node, indent=0):
    """Gibt den AST formatiert aus"""
    prefix = "  " * indent
    if isinstance(node, Program):
        print(f"{prefix}Program:")
        for decl in node.declarations:
            print_ast(decl, indent + 1)
    elif isinstance(node, FunctionDecl):
        print(f"{prefix}FunctionDecl: {node.return_type} {node.name}")
        print(f"{prefix}  Parameters:")
        for param in node.params:
            print_ast(param, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    elif isinstance(node, VarDecl):
        init_str = f" = {node.init_value}" if node.init_value else ""
        print(f"{prefix}VarDecl: {node.var_type} {node.name}{init_str}")
        if node.init_value:
            print_ast(node.init_value, indent + 1)
    elif isinstance(node, CompoundStmt):
        print(f"{prefix}CompoundStmt:")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    elif isinstance(node, ReturnStmt):
        print(f"{prefix}ReturnStmt:")
        if node.value:
            print_ast(node.value, indent + 1)
    elif isinstance(node, IfStmt):
        print(f"{prefix}IfStmt:")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Then:")
        print_ast(node.then_stmt, indent + 2)
        if node.else_stmt:
            print(f"{prefix}  Else:")
            print_ast(node.else_stmt, indent + 2)
    elif isinstance(node, WhileStmt):
        print(f"{prefix}WhileStmt:")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    elif isinstance(node, ForStmt):
        print(f"{prefix}ForStmt:")
        if node.init:
            print(f"{prefix}  Init:")
            print_ast(node.init, indent + 2)
        if node.condition:
            print(f"{prefix}  Condition:")
            print_ast(node.condition, indent + 2)
        if node.increment:
            print(f"{prefix}  Increment:")
            print_ast(node.increment, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    elif isinstance(node, ArrayDecl):
        size_str = f"[{node.size}]" if node.size else "[]"
        print(f"{prefix}ArrayDecl: {node.element_type} {node.name}{size_str}")
        if node.init_values:
            print(f"{prefix}  Initializers:")
            for val in node.init_values:
                print_ast(val, indent + 2)
    elif isinstance(node, ArrayAccess):
        print(f"{prefix}ArrayAccess: {node.array_name}")
        print(f"{prefix}  Index:")
        print_ast(node.index, indent + 2)
    elif isinstance(node, StructDecl):
        print(f"{prefix}StructDecl: {node.name}")
        print(f"{prefix}  Members:")
        for member in node.members:
            print_ast(member, indent + 2)
    elif isinstance(node, StructVarDecl):
        print(f"{prefix}StructVarDecl: struct {node.struct_name} {node.var_name}")
        if node.init_value:
            print(f"{prefix}  Init:")
            print_ast(node.init_value, indent + 2)
    elif isinstance(node, MemberAccess):
        print(f"{prefix}MemberAccess: .{node.member}")
        print(f"{prefix}  Object:")
        print_ast(node.object, indent + 2)
    elif isinstance(node, BinaryOp):
        print(f"{prefix}BinaryOp: {node.op}")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, UnaryOp):
        print(f"{prefix}UnaryOp: {node.op}")
        print_ast(node.operand, indent + 1)
    elif isinstance(node, Assignment):
        print(f"{prefix}Assignment: {node.target} =")
        print_ast(node.value, indent + 1)
    elif isinstance(node, FunctionCall):
        print(f"{prefix}FunctionCall: {node.name}")
        for arg in node.args:
            print_ast(arg, indent + 1)
    elif isinstance(node, Identifier):
        print(f"{prefix}Identifier: {node.name}")
    elif isinstance(node, Literal):
        print(f"{prefix}Literal: {node.value} ({node.lit_type})")

# Beispielverwendung
if __name__ == "__main__":
    c_code = """
    // Struct-Definition
    struct Point {
        int x;
        int y;
    };

    // Funktion mit Arrays
    int sum_array(int arr[], int size) {
        int total = 0;
        for (int i = 0; i < size; i = i + 1) {
            total = total + arr[i];
        }
        return total;
    }

    int main() {
        // Array-Deklaration und Initialisierung
        int numbers[5] = {1, 2, 3, 4, 5};

        // Struct-Variable
        struct Point p;
        p.x = 10;
        p.y = 20;

        // For-Schleife
        int sum = 0;
        for (int i = 0; i < 5; i = i + 1) {
            sum = sum + numbers[i];
        }

        // Array-Zugriff
        int first = numbers[0];

        // While mit Struct
        while (p.x < 15) {
            p.x = p.x + 1;
        }

        return sum;
    }
    """

    # Lexing
    lexer = Lexer(c_code)
    print("=== TOKENS ===")
    for token in lexer.tokens[:30]:  # Erste 30 Tokens
        print(token)
    print("...\n")

    print("=== ABSTRACT SYNTAX TREE ===")
    # Parsing
    parser = Parser(lexer.tokens)
    ast = parser.parse()

    # AST ausgeben
    print_ast(ast)
