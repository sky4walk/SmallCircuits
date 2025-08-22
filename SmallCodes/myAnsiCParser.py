class Token:
    def __init__(self, type, value, line=0):
        self.type = type
        self.value = value
        self.line = line
    
    def __repr__(self):
        return f"Token({self.type}, {self.value}, line={self.line})"

class Tokenizer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.current_pos = 0
        self.current_line = 1
        
        self.keywords = {
            'int', 'char', 'void', 'return', 
            'if', 'else', 'while', 'for'
        }
        self.operators = {
            '+', '-', '*', '/', '=', 
            '==', '!=', '<', '>', '<=', '>='
        }
    
    def is_whitespace(self, char):
        return char in {' ', '\t', '\n', '\r'}
    
    def is_digit(self, char):
        return char in '0123456789'
    
    def is_alpha(self, char):
        return char.isalpha() or char == '_'
    
    def tokenize(self):
        while self.current_pos < len(self.source_code):
            char = self.source_code[self.current_pos]
            
            # Whitespace überspringen
            if self.is_whitespace(char):
                if char == '\n':
                    self.current_line += 1
                self.current_pos += 1
                continue
            
            # Kommentare überspringen
            if char == '/' and self.current_pos + 1 < len(self.source_code):
                next_char = self.source_code[self.current_pos + 1]
                if next_char == '/':
                    while (self.current_pos < len(self.source_code) and 
                           self.source_code[self.current_pos] != '\n'):
                        self.current_pos += 1
                    continue
                elif next_char == '*':
                    while (self.current_pos < len(self.source_code) and 
                           not (self.source_code[self.current_pos] == '*' and 
                                self.current_pos + 1 < len(self.source_code) and 
                                self.source_code[self.current_pos + 1] == '/')):
                        if self.source_code[self.current_pos] == '\n':
                            self.current_line += 1
                        self.current_pos += 1
                    self.current_pos += 2
                    continue
            
            # Zahlen
            if self.is_digit(char):
                number = self.parse_number()
                self.tokens.append(Token('NUMBER', number, self.current_line))
                continue
            
            # Identifier und Keywords
            if self.is_alpha(char):
                identifier = self.parse_identifier()
                token_type = 'KEYWORD' if identifier in self.keywords else 'IDENTIFIER'
                self.tokens.append(Token(token_type, identifier, self.current_line))
                continue
            
            # Operatoren und Sonderzeichen
            if char in '(){}[];,':
                self.tokens.append(Token('PUNCTUATION', char, self.current_line))
                self.current_pos += 1
                continue
            
            # Mehrzeichenoperatoren
            if char in '=!<>':
                operator = self.parse_multi_char_operator(char)
                self.tokens.append(Token('OPERATOR', operator, self.current_line))
                continue
            
            # Einfache Operatoren
            if char in '+-*/':
                self.tokens.append(Token('OPERATOR', char, self.current_line))
                self.current_pos += 1
                continue
            
            raise SyntaxError(f"Unerwartetes Zeichen: {char} in Zeile {self.current_line}")
        
        return self.tokens
    
    def parse_number(self):
        start = self.current_pos
        while (self.current_pos < len(self.source_code) and 
               self.is_digit(self.source_code[self.current_pos])):
            self.current_pos += 1
        return int(self.source_code[start:self.current_pos])
    
    def parse_identifier(self):
        start = self.current_pos
        while (self.current_pos < len(self.source_code) and 
               (self.is_alpha(self.source_code[self.current_pos]) or 
                self.is_digit(self.source_code[self.current_pos]))):
            self.current_pos += 1
        return self.source_code[start:self.current_pos]
    
    def parse_multi_char_operator(self, first_char):
        if self.current_pos + 1 < len(self.source_code):
            next_char = self.source_code[self.current_pos + 1]
            if (first_char + next_char) in {'==', '!=', '<=', '>='}:
                self.current_pos += 2
                return first_char + next_char
        self.current_pos += 1
        return first_char

class ASTNode:
    def __init__(self, type, value=None, children=None):
        self.type = type
        self.value = value
        self.children = children or []

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.symbol_table = {}
    
    def parse(self):
        try:
            return self.parse_program()
        except Exception as e:
            print(f"Parsing-Fehler: {e}")
            print(f"Aktueller Token: {self.tokens[self.current_token_index]}")
            raise
    
    def parse_program(self):
        program_node = ASTNode('PROGRAM')
        
        while self.current_token_index < len(self.tokens):
            function = self.parse_function()
            if function:
                program_node.children.append(function)
            else:
                break
        
        return program_node
    
    def parse_function(self):
        # Speichere Ausgangsposition für Rollback
        start_index = self.current_token_index
        
        try:
            # Rückgabetyp
            if not self.match_type('KEYWORD', {'int', 'void', 'char'}):
                return None
            
            # Funktionsname
            if not self.match_type('IDENTIFIER'):
                self.current_token_index = start_index
                return None
            
            func_name = self.tokens[self.current_token_index - 1].value
            
            # Funktionsparameter
            if not self.match_value('PUNCTUATION', '('):
                self.current_token_index = start_index
                return None
            
            # Parameter parsen (vereinfacht)
            if not self.match_value('PUNCTUATION', ')'):
                self.current_token_index = start_index
                return None
            
            # Funktionskörper
            body = self.parse_block()
            
            if not body:
                self.current_token_index = start_index
                return None
            
            return ASTNode('FUNCTION', {
                'name': func_name, 
                'body': body
            })
        
        except Exception:
            # Rollback bei Fehler
            self.current_token_index = start_index
            return None
    
    def parse_block(self):
        # Speichere Ausgangsposition für Rollback
        start_index = self.current_token_index
        
        try:
            if not self.match_value('PUNCTUATION', '{'):
                return None
            
            block_node = ASTNode('BLOCK')
            
            while not self.match_value('PUNCTUATION', '}'):
                statement = self.parse_statement()
                if statement:
                    block_node.children.append(statement)
                else:
                    break
            
            return block_node
        
        except Exception:
            # Rollback bei Fehler
            self.current_token_index = start_index
            return None
    
    def parse_statement(self):
        # Speichere Ausgangsposition für Rollback
        start_index = self.current_token_index
        
        try:
            # Variablendeklaration
            if self.match_type('KEYWORD', {'int', 'char'}):
                return self.parse_variable_declaration()
            
            # Zuweisungen
            if self.match_type('IDENTIFIER'):
                if self.match_value('OPERATOR', '='):
                    return self.parse_assignment()
                self.current_token_index = start_index
                return None
            
            return None
        
        except Exception:
            # Rollback bei Fehler
            self.current_token_index = start_index
            return None
    
    def parse_variable_declaration(self):
        var_type = self.tokens[self.current_token_index - 1].value
        var_name = self.tokens[self.current_token_index].value
        
        # Symbol-Tabelle aktualisieren
        self.symbol_table[var_name] = {
            'type': var_type,
            'memory_address': len(self.symbol_table) * 2 + 0x0200
        }
        
        # Initialisierung prüfen
        if self.match_value('OPERATOR', '='):
            value = self.tokens[self.current_token_index].value
            self.current_token_index += 1
            return ASTNode('VARIABLE_DECLARATION', {
                'name': var_name,
                'type': var_type,
                'value': value
            })
        
        return ASTNode('VARIABLE_DECLARATION', {
            'name': var_name,
            'type': var_type
        })
    
    def parse_assignment(self):
        var_name = self.tokens[self.current_token_index - 2].value
        value = self.tokens[self.current_token_index].value
        self.current_token_index += 1
        
        return ASTNode('ASSIGNMENT', {
            'variable': var_name,
            'value': value
        })
    
    def match_type(self, token_type, expected_types=None):
        if self.current_token_index >= len(self.tokens):
            return False
        
        current_token = self.tokens[self.current_token_index]
        
        if current_token.type == token_type:
            if expected_types is None or current_token.value in expected_types:
                self.current_token_index += 1
                return True
        
        return False
    
    def match_value(self, token_type, expected_value):
        if self.current_token_index >= len(self.tokens):
            return False
        
        current_token = self.tokens[self.current_token_index]
        
        if (current_token.type == token_type and 
            current_token.value == expected_value):
            self.current_token_index += 1
            return True
        
        return False

# Rest des Codes bleibt unverändert wie im vorherigen Beispiel

def main():
    # Beispiel-C-Code
    c_code = """
    int main() {
        int x = 10;
        int y = 20;
        int z = 30;
    }
    """
    
    try:
        # Tokenisierung
        tokenizer = Tokenizer(c_code)
        tokens = tokenizer.tokenize()
        
        print("Tokens:")
        for token in tokens:
            print(token)
        
        # Parsing
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Codegenerierung
        code_generator = CodeGenerator(ast, parser.symbol_table)
        assembly_output = code_generator.generate()
        
        # Ausgabe des Assembler-Codes
        print("\nGenerierter 6502 Assembler:")
        print(assembly_output)
    
    except Exception as e:
        print(f"Fehler während der Kompilierung: {e}")

if __name__ == "__main__":
    main()