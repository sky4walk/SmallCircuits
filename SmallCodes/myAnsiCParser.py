# AST Knoten-Definitionen (ohne dataclass, einfache Klassen)
class ASTNode:
    """Basis-Klasse für alle AST-Knoten"""
    pass

class Program(ASTNode):
    def __init__(self, declarations):
        self.declarations = declarations  # Liste von Deklarationen

class FunctionDecl(ASTNode):
    def __init__(self, return_type, name, params, body):
        self.return_type = return_type
        self.name = name
        self.params = params  # Liste von VarDecl
        self.body = body      # CompoundStmt

class VarDecl(ASTNode):
    def __init__(self, var_type, name, init_value=None):
        self.var_type = var_type
        self.name = name
        self.init_value = init_value  # Kann None sein

class CompoundStmt(ASTNode):
    def __init__(self, statements):
        self.statements = statements  # Liste von Statements

class ReturnStmt(ASTNode):
    def __init__(self, value):
        self.value = value  # Kann None sein

class IfStmt(ASTNode):
    def __init__(self, condition, then_stmt, else_stmt=None):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt  # Kann None sein

class WhileStmt(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class BinaryOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class Assignment(ASTNode):
    def __init__(self, target, value):
        self.target = target
        self.value = value

class FunctionCall(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args  # Liste von Ausdrücken

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class Literal(ASTNode):
    def __init__(self, value, lit_type):
        self.value = value      # int, float oder string
        self.lit_type = lit_type  # 'int', 'float', 'string'

class ArrayDecl(ASTNode):
    def __init__(self, element_type, name, size, init_values=None):
        self.element_type = element_type
        self.name = name
        self.size = size          # Kann None sein
        self.init_values = init_values  # Liste oder None

class ArrayAccess(ASTNode):
    def __init__(self, array_name, index):
        self.array_name = array_name
        self.index = index

class StructDecl(ASTNode):
    def __init__(self, name, members):
        self.name = name
        self.members = members  # Liste von VarDecl

class StructVarDecl(ASTNode):
    def __init__(self, struct_name, var_name, init_value=None):
        self.struct_name = struct_name
        self.var_name = var_name
        self.init_value = init_value  # Kann None sein

class MemberAccess(ASTNode):
    def __init__(self, obj, member):
        self.object = obj
        self.member = member

class ForStmt(ASTNode):
    def __init__(self, init, condition, increment, body):
        self.init = init          # Kann None sein
        self.condition = condition  # Kann None sein
        self.increment = increment  # Kann None sein
        self.body = body

class PointerDecl(ASTNode):
    def __init__(self, base_type, name, init_value=None):
        self.base_type = base_type  # Typ auf den gezeigt wird
        self.name = name
        self.init_value = init_value  # Kann None sein

class Dereference(ASTNode):
    def __init__(self, pointer):
        self.pointer = pointer  # Der Pointer-Ausdruck

class AddressOf(ASTNode):
    def __init__(self, operand):
        self.operand = operand  # Variable deren Adresse genommen wird

# Lexer (Tokenizer)
class Token:
    def __init__(self, type_, value, line=0):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []
        self.line = 1
        self.tokenize()

    def current_char(self):
        """Gibt das aktuelle Zeichen zurück"""
        if self.pos < len(self.code):
            return self.code[self.pos]
        return None

    def peek(self, offset=1):
        """Schaut voraus ohne Position zu ändern"""
        peek_pos = self.pos + offset
        if peek_pos < len(self.code):
            return self.code[peek_pos]
        return None

    def advance(self):
        """Bewegt die Position um 1 vorwärts"""
        if self.pos < len(self.code):
            if self.code[self.pos] == '\n':
                self.line += 1
            self.pos += 1

    def skip_whitespace(self):
        """Überspringt Whitespace"""
        while self.current_char() and self.current_char() in ' \t\n\r':
            self.advance()

    def skip_single_line_comment(self):
        """Überspringt einzeilige Kommentare //..."""
        self.advance()  # /
        self.advance()  # /
        while self.current_char() and self.current_char() != '\n':
            self.advance()

    def skip_multi_line_comment(self):
        """Überspringt mehrzeilige Kommentare /* ... */"""
        self.advance()  # /
        self.advance()  # *
        while self.current_char():
            if self.current_char() == '*' and self.peek() == '/':
                self.advance()  # *
                self.advance()  # /
                break
            self.advance()

    def read_number(self):
        """Liest eine Zahl (int oder float)"""
        num_str = ''
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            num_str += self.current_char()
            self.advance()
        return num_str

    def read_string(self):
        """Liest einen String "..." """
        string_val = ''
        self.advance()  # Öffnendes "
        while self.current_char() and self.current_char() != '"':
            string_val += self.current_char()
            self.advance()
        if self.current_char() == '"':
            self.advance()  # Schließendes "
        return '"' + string_val + '"'

    def read_identifier_or_keyword(self):
        """Liest einen Identifier oder Keyword"""
        id_str = ''
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            id_str += self.current_char()
            self.advance()
        return id_str

    def is_keyword(self, word):
        """Prüft ob ein Wort ein Keyword ist"""
        keywords = ['int', 'float', 'void', 'return', 'if', 'else', 'while', 'for', 'struct']
        return word in keywords

    def tokenize(self):
        """Hauptmethode für Tokenisierung"""
        while self.pos < len(self.code):
            self.skip_whitespace()

            ch = self.current_char()
            if ch is None:
                break

            # Kommentare
            if ch == '/' and self.peek() == '/':
                self.skip_single_line_comment()
                continue

            if ch == '/' and self.peek() == '*':
                self.skip_multi_line_comment()
                continue

            # Zahlen
            if ch.isdigit():
                num = self.read_number()
                self.tokens.append(Token('NUMBER', num, self.line))
                continue

            # Strings
            if ch == '"':
                string = self.read_string()
                self.tokens.append(Token('STRING', string, self.line))
                continue

            # Identifiers und Keywords
            if ch.isalpha() or ch == '_':
                word = self.read_identifier_or_keyword()
                if self.is_keyword(word):
                    self.tokens.append(Token('KEYWORD', word, self.line))
                else:
                    self.tokens.append(Token('IDENTIFIER', word, self.line))
                continue

            # Zwei-Zeichen-Operatoren
            if ch == '<' and self.peek() == '=':
                self.tokens.append(Token('LE', '<=', self.line))
                self.advance()
                self.advance()
                continue

            if ch == '>' and self.peek() == '=':
                self.tokens.append(Token('GE', '>=', self.line))
                self.advance()
                self.advance()
                continue

            if ch == '=' and self.peek() == '=':
                self.tokens.append(Token('EQ', '==', self.line))
                self.advance()
                self.advance()
                continue

            if ch == '!' and self.peek() == '=':
                self.tokens.append(Token('NE', '!=', self.line))
                self.advance()
                self.advance()
                continue

            # Ein-Zeichen-Tokens
            single_char_tokens = {
                '(': 'LPAREN',
                ')': 'RPAREN',
                '{': 'LBRACE',
                '}': 'RBRACE',
                '[': 'LBRACKET',
                ']': 'RBRACKET',
                ';': 'SEMICOLON',
                ',': 'COMMA',
                '.': 'DOT',
                '=': 'ASSIGN',
                '+': 'PLUS',
                '-': 'MINUS',
                '*': 'MULT',
                '/': 'DIV',
                '<': 'LT',
                '>': 'GT',
                '&': 'AMPERSAND',
            }

            if ch in single_char_tokens:
                self.tokens.append(Token(single_char_tokens[ch], ch, self.line))
                self.advance()
                continue

            # Unbekanntes Zeichen
            raise SyntaxError(f"Unbekanntes Zeichen: '{ch}' in Zeile {self.line}")
            self.advance()

# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

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
        if token is None:
            return False
        return token.type in types

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

            # Pointer-Check
            if self.match('MULT'):
                return self.parse_pointer_or_variable(type_token.value)

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

        # Pointer-Parameter (z.B. int* ptr)
        is_pointer = False
        if self.match('MULT'):
            self.consume('MULT')
            is_pointer = True

        var_name = self.consume('IDENTIFIER').value

        # Array-Parameter (z.B. int arr[])
        if self.match('LBRACKET'):
            self.consume('LBRACKET')
            # Optional: Array-Größe (meist leer bei Parametern)
            if not self.match('RBRACKET'):
                size = self.parse_expression()
            self.consume('RBRACKET')
            var_type = var_type + "[]"
        elif is_pointer:
            var_type = var_type + "*"

        return VarDecl(var_type, var_name)

    def parse_variable(self, var_type, var_name):
        """Parsing einer Variablendeklaration"""
        init_value = None
        if self.match('ASSIGN'):
            self.consume('ASSIGN')
            init_value = self.parse_expression()
        self.consume('SEMICOLON')
        return VarDecl(var_type, var_name, init_value)

    def parse_pointer_or_variable(self, var_type):
        """Parsing von Pointer- oder Variablendeklaration"""
        # Pointer-Deklaration (z.B. int* ptr)
        is_pointer = False
        if self.match('MULT'):
            self.consume('MULT')
            is_pointer = True

        var_name = self.consume('IDENTIFIER').value

        if is_pointer:
            init_value = None
            if self.match('ASSIGN'):
                self.consume('ASSIGN')
                init_value = self.parse_expression()
            self.consume('SEMICOLON')
            return PointerDecl(var_type, var_name, init_value)
        else:
            return self.parse_variable(var_type, var_name)

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

                # Pointer-Deklaration in Statement
                if self.match('MULT'):
                    return self.parse_pointer_or_variable(type_val)

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

        # Pointer-Dereferenzierung-Zuweisung (*ptr = value)
        if self.match('MULT'):
            self.consume('MULT')
            ptr_name = self.consume('IDENTIFIER').value
            self.consume('ASSIGN')
            value = self.parse_expression()
            self.consume('SEMICOLON')
            return Assignment(f"*{ptr_name}", value)

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

        # Pointer-Dereferenzierung (*ptr)
        if self.match('MULT'):
            self.consume('MULT')
            operand = self.parse_unary()
            return Dereference(operand)

        # Address-of Operator (&var)
        if self.match('AMPERSAND'):
            self.consume('AMPERSAND')
            operand = self.parse_primary()
            return AddressOf(operand)

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
    elif isinstance(node, PointerDecl):
        print(f"{prefix}PointerDecl: {node.base_type}* {node.name}")
        if node.init_value:
            print(f"{prefix}  Init:")
            print_ast(node.init_value, indent + 2)
    elif isinstance(node, Dereference):
        print(f"{prefix}Dereference: *")
        print_ast(node.pointer, indent + 1)
    elif isinstance(node, AddressOf):
        print(f"{prefix}AddressOf: &")
        print_ast(node.operand, indent + 1)
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

# Code-Generator für MOS 6510 Assembler
class CodeGenerator6510:
    """Generiert 6510 Assembler-Code aus dem AST"""

    def __init__(self):
        self.code = []  # Liste von Assembler-Zeilen
        self.label_counter = 0
        self.zero_page_offset = 0x02  # Zero-Page Variablen ab $02
        self.var_to_zp = {}  # Variable -> Zero-Page Adresse
        self.temp_counter = 0
        self.array_base_addresses = {}  # Array -> Start-Adresse
        self.current_memory_offset = 0x0400  # Start bei $0400 (nach Zero-Page und Stack)

    def new_label(self, prefix="L"):
        """Erzeugt ein neues Label"""
        label = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return label

    def allocate_zero_page(self, var_name):
        """Allokiert Zero-Page Speicher für Variable"""
        if var_name not in self.var_to_zp:
            self.var_to_zp[var_name] = self.zero_page_offset
            self.zero_page_offset += 1
            if self.zero_page_offset > 0xFF:
                raise Exception("Zero-Page voll!")
        return self.var_to_zp[var_name]

    def emit(self, line):
        """Fügt eine Assembler-Zeile hinzu"""
        self.code.append(line)

    def generate(self, node):
        """Haupt-Generator-Methode"""
        if isinstance(node, Program):
            self.emit("; MOS 6510 Assembler Code")
            self.emit("; Generiert aus C-Code")
            self.emit("")
            for decl in node.declarations:
                self.generate(decl)
            return '\n'.join(self.code)

        elif isinstance(node, FunctionDecl):
            self.emit(f"; Funktion: {node.return_type} {node.name}")
            self.emit(f"{node.name}:")

            # Parameter in Zero-Page speichern
            for i, param in enumerate(node.params):
                zp_addr = self.allocate_zero_page(param.name)
                self.emit(f"    ; Parameter {param.name} bei ${zp_addr:02X}")

            # Body generieren
            self.generate(node.body)

            self.emit("    RTS")
            self.emit("")

        elif isinstance(node, CompoundStmt):
            for stmt in node.statements:
                self.generate(stmt)

        elif isinstance(node, VarDecl):
            # Variable allokieren
            zp_addr = self.allocate_zero_page(node.name)
            self.emit(f"    ; Variable {node.var_type} {node.name} bei ${zp_addr:02X}")

            # Initialisierung
            if node.init_value:
                result_reg = self.generate_expression(node.init_value)
                self.emit(f"    STA ${zp_addr:02X}    ; {node.name} = Akkumulator")

        elif isinstance(node, ArrayDecl):
            # Array im Speicher allokieren
            if node.size and isinstance(node.size, Literal):
                array_size = node.size.value
            else:
                array_size = len(node.init_values) if node.init_values else 10

            # Array-Start-Adresse speichern
            self.array_base_addresses[node.name] = self.current_memory_offset
            self.emit(f"    ; Array {node.element_type} {node.name}[{array_size}] bei ${self.current_memory_offset:04X}")

            # Pointer auf Array in Zero-Page
            ptr_lo = self.allocate_zero_page(f"{node.name}_ptr_lo")
            ptr_hi = self.allocate_zero_page(f"{node.name}_ptr_hi")

            self.emit(f"    LDA #<${self.current_memory_offset:04X}")
            self.emit(f"    STA ${ptr_lo:02X}")
            self.emit(f"    LDA #>${self.current_memory_offset:04X}")
            self.emit(f"    STA ${ptr_hi:02X}")

            # Array initialisieren falls Werte vorhanden
            if node.init_values:
                for i, val in enumerate(node.init_values):
                    if isinstance(val, Literal):
                        addr = self.current_memory_offset + i
                        self.emit(f"    LDA #${val.value & 0xFF:02X}")
                        self.emit(f"    STA ${addr:04X}")

            self.current_memory_offset += array_size

        elif isinstance(node, PointerDecl):
            # Pointer allokieren (2 Bytes: lo/hi)
            ptr_lo = self.allocate_zero_page(f"{node.name}_lo")
            ptr_hi = self.allocate_zero_page(f"{node.name}_hi")
            self.emit(f"    ; Pointer {node.base_type}* {node.name} bei ${ptr_lo:02X}/${ptr_hi:02X}")

            if node.init_value:
                # Adresse laden (z.B. &variable)
                result = self.generate_expression(node.init_value)
                self.emit(f"    STA ${ptr_lo:02X}")
                self.emit(f"    STX ${ptr_hi:02X}")

        elif isinstance(node, Assignment):
            # Wert berechnen
            result_reg = self.generate_expression(node.value)

            # In Variable speichern
            var_name = node.target

            # Pointer-Dereferenzierung (*ptr = value)
            if var_name.startswith('*'):
                ptr_name = var_name[1:]
                ptr_lo = self.var_to_zp.get(f"{ptr_name}_lo")
                ptr_hi = self.var_to_zp.get(f"{ptr_name}_hi")
                if ptr_lo and ptr_hi:
                    # Indirekte Adressierung via Zero-Page
                    self.emit(f"    LDY #$00")
                    self.emit(f"    STA (${ptr_lo:02X}),Y    ; *{ptr_name} = A")

            # Array-Zugriff (arr[index] = value)
            elif '[' in var_name:
                # Vereinfachte Behandlung für konstante Indices
                self.emit(f"    ; Array-Zuweisung {var_name}")

            # Normale Variable
            elif var_name in self.var_to_zp:
                zp_addr = self.var_to_zp[var_name]
                self.emit(f"    STA ${zp_addr:02X}    ; {var_name} = Akkumulator")

        elif isinstance(node, ReturnStmt):
            if node.value:
                result_reg = self.generate_expression(node.value)
                self.emit(f"    ; Return-Wert in Akkumulator")
            self.emit("    RTS")

        elif isinstance(node, IfStmt):
            else_label = self.new_label("ELSE")
            end_label = self.new_label("ENDIF")

            # Condition auswerten
            self.generate_expression(node.condition)
            self.emit(f"    CMP #$00")
            self.emit(f"    BEQ {else_label}")

            # Then-Block
            self.generate(node.then_stmt)
            self.emit(f"    JMP {end_label}")

            # Else-Block
            self.emit(f"{else_label}:")
            if node.else_stmt:
                self.generate(node.else_stmt)

            self.emit(f"{end_label}:")

        elif isinstance(node, WhileStmt):
            loop_label = self.new_label("WHILE")
            end_label = self.new_label("ENDWHILE")

            self.emit(f"{loop_label}:")

            # Condition prüfen
            self.generate_expression(node.condition)
            self.emit(f"    CMP #$00")
            self.emit(f"    BEQ {end_label}")

            # Body
            self.generate(node.body)
            self.emit(f"    JMP {loop_label}")

            self.emit(f"{end_label}:")

        elif isinstance(node, ForStmt):
            loop_label = self.new_label("FOR")
            end_label = self.new_label("ENDFOR")

            # Init
            if node.init:
                self.generate(node.init)

            self.emit(f"{loop_label}:")

            # Condition
            if node.condition:
                self.generate_expression(node.condition)
                self.emit(f"    CMP #$00")
                self.emit(f"    BEQ {end_label}")

            # Body
            self.generate(node.body)

            # Increment
            if node.increment:
                self.generate(node.increment)

            self.emit(f"    JMP {loop_label}")
            self.emit(f"{end_label}:")

    def generate_expression(self, node):
        """Generiert Code für Ausdrücke, Ergebnis im Akkumulator"""

        if isinstance(node, Literal):
            if node.lit_type == 'int':
                value = node.value & 0xFF  # 8-bit begrenzen
                self.emit(f"    LDA #${value:02X}    ; Literal {node.value}")
            return 'A'

        elif isinstance(node, Identifier):
            var_name = node.name
            if var_name in self.var_to_zp:
                zp_addr = self.var_to_zp[var_name]
                self.emit(f"    LDA ${zp_addr:02X}    ; {var_name}")
            return 'A'

        elif isinstance(node, BinaryOp):
            if node.op == '+':
                # Linke Seite in Akkumulator
                self.generate_expression(node.left)

                # Akkumulator temporär speichern
                temp_zp = self.allocate_zero_page(f"_temp{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${temp_zp:02X}    ; Temp speichern")

                # Rechte Seite berechnen
                self.generate_expression(node.right)

                # Addition
                self.emit(f"    CLC")
                self.emit(f"    ADC ${temp_zp:02X}    ; Addition")
                return 'A'

            elif node.op == '-':
                # Rechte Seite in Akkumulator
                self.generate_expression(node.right)

                # Akkumulator temporär speichern
                temp_zp = self.allocate_zero_page(f"_temp{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${temp_zp:02X}    ; Temp speichern")

                # Linke Seite
                self.generate_expression(node.left)

                # Subtraktion
                self.emit(f"    SEC")
                self.emit(f"    SBC ${temp_zp:02X}    ; Subtraktion")
                return 'A'

            elif node.op == '*':
                # Multiplikation auf dem 6510 (keine MUL-Instruktion!)
                # Wir verwenden wiederholte Addition
                self.emit(f"    ; Multiplikation (wiederholte Addition)")

                # Rechte Seite (Multiplikator)
                self.generate_expression(node.right)
                multiplier_zp = self.allocate_zero_page(f"_mult{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${multiplier_zp:02X}")

                # Linke Seite (Multiplikand)
                self.generate_expression(node.left)
                multiplicand_zp = self.allocate_zero_page(f"_mult{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${multiplicand_zp:02X}")

                # Ergebnis initialisieren
                result_zp = self.allocate_zero_page(f"_mult{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    LDA #$00")
                self.emit(f"    STA ${result_zp:02X}")

                # Multiplikations-Schleife
                mult_loop = self.new_label("MULT_LOOP")
                mult_end = self.new_label("MULT_END")

                self.emit(f"{mult_loop}:")
                self.emit(f"    LDA ${multiplier_zp:02X}")
                self.emit(f"    BEQ {mult_end}")
                self.emit(f"    LDA ${result_zp:02X}")
                self.emit(f"    CLC")
                self.emit(f"    ADC ${multiplicand_zp:02X}")
                self.emit(f"    STA ${result_zp:02X}")
                self.emit(f"    DEC ${multiplier_zp:02X}")
                self.emit(f"    JMP {mult_loop}")
                self.emit(f"{mult_end}:")
                self.emit(f"    LDA ${result_zp:02X}")
                return 'A'

            elif node.op == '/':
                # Division (wiederholte Subtraktion)
                self.emit(f"    ; Division (wiederholte Subtraktion)")

                # Divisor
                self.generate_expression(node.right)
                divisor_zp = self.allocate_zero_page(f"_div{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${divisor_zp:02X}")

                # Dividend
                self.generate_expression(node.left)
                dividend_zp = self.allocate_zero_page(f"_div{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${dividend_zp:02X}")

                # Quotient initialisieren
                quotient_zp = self.allocate_zero_page(f"_div{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    LDA #$00")
                self.emit(f"    STA ${quotient_zp:02X}")

                # Divisions-Schleife
                div_loop = self.new_label("DIV_LOOP")
                div_end = self.new_label("DIV_END")

                self.emit(f"{div_loop}:")
                self.emit(f"    LDA ${dividend_zp:02X}")
                self.emit(f"    CMP ${divisor_zp:02X}")
                self.emit(f"    BCC {div_end}")
                self.emit(f"    SEC")
                self.emit(f"    SBC ${divisor_zp:02X}")
                self.emit(f"    STA ${dividend_zp:02X}")
                self.emit(f"    INC ${quotient_zp:02X}")
                self.emit(f"    JMP {div_loop}")
                self.emit(f"{div_end}:")
                self.emit(f"    LDA ${quotient_zp:02X}")
                return 'A'

            elif node.op in ['<', '>', '<=', '>=', '==', '!=']:
                # Linke Seite
                self.generate_expression(node.left)
                temp_zp = self.allocate_zero_page(f"_temp{self.temp_counter}")
                self.temp_counter += 1
                self.emit(f"    STA ${temp_zp:02X}")

                # Rechte Seite
                self.generate_expression(node.right)

                # Vergleich
                self.emit(f"    CMP ${temp_zp:02X}")

                # Ergebnis setzen (vereinfacht: 0 oder 1)
                true_label = self.new_label("TRUE")
                end_label = self.new_label("ENDCMP")

                if node.op == '<':
                    self.emit(f"    BCC {true_label}")
                elif node.op == '>':
                    self.emit(f"    BEQ {end_label}")
                    self.emit(f"    BCS {true_label}")
                elif node.op == '==':
                    self.emit(f"    BEQ {true_label}")
                elif node.op == '!=':
                    self.emit(f"    BNE {true_label}")

                # False
                self.emit(f"    LDA #$00")
                self.emit(f"    JMP {end_label}")

                # True
                self.emit(f"{true_label}:")
                self.emit(f"    LDA #$01")

                self.emit(f"{end_label}:")
                return 'A'

        elif isinstance(node, UnaryOp):
            if node.op == '-':
                # Operand berechnen
                self.generate_expression(node.operand)
                # Negation (Two's Complement)
                self.emit(f"    EOR #$FF    ; Bitweise invertieren")
                self.emit(f"    CLC")
                self.emit(f"    ADC #$01    ; +1 für Two's Complement")
                return 'A'

        elif isinstance(node, FunctionCall):
            # Vereinfachte Funktionsaufrufe
            # Parameter müssten auf Stack oder in Zero-Page übergeben werden
            self.emit(f"    JSR {node.name}")
            return 'A'

        elif isinstance(node, ArrayAccess):
            # Array-Zugriff: arr[index]
            array_name = node.array_name

            if array_name in self.array_base_addresses:
                # Index berechnen
                self.generate_expression(node.index)

                # Index in Y-Register
                self.emit(f"    TAY")

                # Pointer auf Array laden
                ptr_lo = self.var_to_zp.get(f"{array_name}_ptr_lo")
                ptr_hi = self.var_to_zp.get(f"{array_name}_ptr_hi")

                if ptr_lo and ptr_hi:
                    # Indizierter Zugriff
                    self.emit(f"    LDA (${ptr_lo:02X}),Y    ; {array_name}[index]")
                return 'A'

        elif isinstance(node, Dereference):
            # Pointer-Dereferenzierung: *ptr
            if isinstance(node.pointer, Identifier):
                ptr_name = node.pointer.name
                ptr_lo = self.var_to_zp.get(f"{ptr_name}_lo")
                ptr_hi = self.var_to_zp.get(f"{ptr_name}_hi")

                if ptr_lo and ptr_hi:
                    self.emit(f"    LDY #$00")
                    self.emit(f"    LDA (${ptr_lo:02X}),Y    ; *{ptr_name}")
                return 'A'

        elif isinstance(node, AddressOf):
            # Address-of: &variable
            if isinstance(node.operand, Identifier):
                var_name = node.operand.name
                if var_name in self.var_to_zp:
                    # Adresse einer Zero-Page Variable
                    zp_addr = self.var_to_zp[var_name]
                    self.emit(f"    LDA #${zp_addr:02X}    ; Low-Byte von &{var_name}")
                    self.emit(f"    LDX #$00    ; High-Byte")
                    return 'A'
                elif var_name in self.array_base_addresses:
                    # Adresse eines Arrays
                    addr = self.array_base_addresses[var_name]
                    self.emit(f"    LDA #<${addr:04X}    ; Low-Byte von &{var_name}")
                    self.emit(f"    LDX #>${addr:04X}    ; High-Byte")
                    return 'A'

        return None

# Beispielverwendung
if __name__ == "__main__":
    c_code = """
    // Einfache Multiplikation
    int multiply(int a, int b) {
        return a * b;
    }

    // Array-Beispiel
    int sum_array(int arr[], int size) {
        int total = 0;
        for (int i = 0; i < size; i = i + 1) {
            total = total + arr[i];
        }
        return total;
    }

    // Pointer-Beispiel
    void increment_value(int* ptr) {
        int val = *ptr;
        val = val + 1;
        *ptr = val;
    }

    int main() {
        // Array mit Multiplikation
        int numbers[3] = {2, 4, 6};
        int result = multiply(5, 3);

        // Pointer-Verwendung
        int x = 10;
        int* px = &x;
        increment_value(px);

        return x;
    }
    """

    # Lexing
    lexer = Lexer(c_code)
    print("=== TOKENS (erste 30) ===")
    for token in lexer.tokens[:30]:
        print(token)
    print("...\n")

    print("=== ABSTRACT SYNTAX TREE ===")
    # Parsing
    parser = Parser(lexer.tokens)
    ast = parser.parse()

    # AST ausgeben (nur erste Funktion)
    if ast.declarations:
        print("Erste Funktion:")
        print_ast(ast.declarations[0])

    print("\n=== MOS 6510 ASSEMBLER CODE ===")
    # Code-Generierung
    codegen = CodeGenerator6510()
    asm_code = codegen.generate(ast)
    print(asm_code)
