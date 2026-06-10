import re
import os
import shutil
import subprocess
import platform
import webbrowser
import fnmatch
from dataclasses import dataclass
from enum import Enum
from typing import List, Any, Dict, Optional

# ----- Токены -----
class TokenType(Enum):
    # Команды
    SAY = 'SAY'
    SET = 'SET'
    OPEN = 'OPEN'
    PING = 'PING'
    BROWSE = 'BROWSE'
    LOOP = 'LOOP'
    CALL = 'CALL'
    LABEL = 'LABEL'
    RETURN = 'RETURN'
    NDIR = 'NDIR'
    DELETE = 'DELETE'
    QUERY = 'QUERY'
    INS = 'INS'
    INS_WR = 'INS_WR'
    INS_CW = 'INS_CW'
    DIR_S = 'DIR_S'
    INP = 'INP'
    
    # Типы данных
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    IDENTIFIER = 'IDENTIFIER'
    
    # Операторы и символы
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    MULTIPLY = 'MULTIPLY'
    DIVIDE = 'DIVIDE'
    EQUALS = 'EQUALS'
    EQUALS_EQUALS = 'EQUALS_EQUALS'
    NOT_EQUALS = 'NOT_EQUALS'
    LESS = 'LESS'
    LESS_EQUAL = 'LESS_EQUAL'
    GREATER = 'GREATER'
    GREATER_EQUAL = 'GREATER_EQUAL'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    SEMICOLON = 'SEMICOLON'
    COMMA = 'COMMA'

@dataclass
class Token:
    type: TokenType
    value: Any = None

# ----- Лексер -----
def lex(code: str) -> List[Token]:
    tokens = []
    keywords = {
        'say': TokenType.SAY,
        'print': TokenType.SAY,
        'set': TokenType.SET,
        'open': TokenType.OPEN,
        'ping': TokenType.PING,
        'browse': TokenType.BROWSE,
        'loop': TokenType.LOOP,
        'call': TokenType.CALL,
        'return': TokenType.RETURN,
        'ndir': TokenType.NDIR,
        'del': TokenType.DELETE,
        'query': TokenType.QUERY,
        'inp': TokenType.INP,
    }
    
    i = 0
    while i < len(code):
        # Пропускаем пробелы
        if code[i].isspace():
            i += 1
            continue
        
        # Числа
        if code[i].isdigit():
            num = ''
            while i < len(code) and (code[i].isdigit() or code[i] == '.'):
                num += code[i]
                i += 1
            if '.' in num:
                tokens.append(Token(TokenType.NUMBER, float(num)))
            else:
                tokens.append(Token(TokenType.NUMBER, int(num)))
            continue
        
        # Строки в кавычках
        if code[i] == '"':
            i += 1
            string = ''
            while i < len(code) and code[i] != '"':
                string += code[i]
                i += 1
            i += 1
            tokens.append(Token(TokenType.STRING, string))
            continue
        
        # Метки (>имя)
        if code[i] == '>':
            i += 1
            label_name = ''
            while i < len(code) and (code[i].isalpha() or code[i].isdigit() or code[i] == '_'):
                label_name += code[i]
                i += 1
            if not label_name:
                raise SyntaxError('Empty label name after >')
            tokens.append(Token(TokenType.LABEL, label_name))
            continue
        
        # Специальная обработка 'dir /s'
        if i + 3 < len(code) and code[i:i+3].lower() == 'dir':
            i += 3
            # Пропускаем пробелы
            while i < len(code) and code[i].isspace():
                i += 1
            # Проверяем флаг /s
            if i + 1 < len(code) and code[i:i+2].lower() == '/s':
                tokens.append(Token(TokenType.DIR_S))
                i += 2
            else:
                tokens.append(Token(TokenType.IDENTIFIER, 'dir'))
            continue
        
        # Специальная обработка ins с флагами
        if i + 2 < len(code) and code[i:i+3].lower() == 'ins':
            i += 3
            # Пропускаем пробелы
            while i < len(code) and code[i].isspace():
                i += 1
            # Проверяем флаги
            if i + 1 < len(code) and code[i:i+2].lower() == 'wr':
                tokens.append(Token(TokenType.INS_WR))
                i += 2
            elif i + 1 < len(code) and code[i:i+2].lower() == 'cw':
                tokens.append(Token(TokenType.INS_CW))
                i += 2
            else:
                tokens.append(Token(TokenType.INS))
            continue
        
        # Буквы (ключевые слова или идентификаторы)
        if code[i].isalpha():
            word = ''
            while i < len(code) and (code[i].isalpha() or code[i].isdigit() or code[i] == '_'):
                word += code[i]
                i += 1
            if word in keywords:
                tokens.append(Token(keywords[word]))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, word))
            continue
        
        # Операторы и символы
        char_map = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '=': TokenType.EQUALS,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
        }
        
        # Двухсимвольные операторы
        if i + 1 < len(code) and code[i:i+2] == '==':
            tokens.append(Token(TokenType.EQUALS_EQUALS))
            i += 2
            continue
        elif i + 1 < len(code) and code[i:i+2] == '!=':
            tokens.append(Token(TokenType.NOT_EQUALS))
            i += 2
            continue
        elif i + 1 < len(code) and code[i:i+2] == '<=':
            tokens.append(Token(TokenType.LESS_EQUAL))
            i += 2
            continue
        elif i + 1 < len(code) and code[i:i+2] == '>=':
            tokens.append(Token(TokenType.GREATER_EQUAL))
            i += 2
            continue
        elif code[i] == '<':
            tokens.append(Token(TokenType.LESS))
            i += 1
            continue
        elif code[i] == '>':
            tokens.append(Token(TokenType.GREATER))
            i += 1
            continue
        
        if code[i] in char_map:
            tokens.append(Token(char_map[code[i]]))
            i += 1
        else:
            raise SyntaxError(f'Unexpected char: {code[i]}')
    
    return tokens

# ----- Интерпретатор -----
class Interpreter:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.variables: Dict[str, Any] = {}
        self.labels: Dict[str, Dict] = {}  # имя -> {'pos': int, 'params': List[str], 'body_end': int}
        self.call_stack: List[Dict] = []
        self.collect_labels()
    
    def collect_labels(self):
        """Первый проход: запоминаем позиции всех меток и их параметры"""
        pos = 0
        while pos < len(self.tokens):
            if self.tokens[pos].type == TokenType.LABEL:
                label_name = self.tokens[pos].value
                pos += 1
                
                # Парсим параметры, если есть
                params = []
                if pos < len(self.tokens) and self.tokens[pos].type == TokenType.LPAREN:
                    pos += 1  # пропускаем (
                    while pos < len(self.tokens) and self.tokens[pos].type != TokenType.RPAREN:
                        if self.tokens[pos].type == TokenType.IDENTIFIER:
                            params.append(self.tokens[pos].value)
                        pos += 1
                        if pos < len(self.tokens) and self.tokens[pos].type == TokenType.COMMA:
                            pos += 1
                    pos += 1  # пропускаем )
                
                # Ищем тело метки (должен быть {)
                body_start = pos
                brace_count = 0
                while pos < len(self.tokens):
                    if self.tokens[pos].type == TokenType.LBRACE:
                        brace_count += 1
                    elif self.tokens[pos].type == TokenType.RBRACE:
                        brace_count -= 1
                        if brace_count == 0:
                            break
                    pos += 1
                
                self.labels[label_name] = {
                    'pos': body_start,
                    'params': params,
                    'body_end': pos
                }
            pos += 1
    
    def peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def consume(self, expected_type: TokenType = None) -> Token:
        token = self.peek()
        if not token:
            raise SyntaxError('Unexpected end of input')
        if expected_type and token.type != expected_type:
            raise SyntaxError(f'Expected {expected_type}, got {token.type}')
        self.pos += 1
        return token
    
    def parse_expression(self) -> Any:
        """Парсит арифметическое выражение или строку"""
        return self.parse_equality()
    
    def parse_equality(self) -> Any:
        left = self.parse_comparison()
        while True:
            token = self.peek()
            if token and token.type in [TokenType.EQUALS_EQUALS, TokenType.NOT_EQUALS]:
                op = self.consume().type
                right = self.parse_comparison()
                if op == TokenType.EQUALS_EQUALS:
                    left = left == right
                else:
                    left = left != right
            else:
                break
        return left
    
    def parse_comparison(self) -> Any:
        left = self.parse_add()
        while True:
            token = self.peek()
            if token and token.type in [TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL]:
                op = self.consume().type
                right = self.parse_add()
                if op == TokenType.LESS:
                    left = left < right
                elif op == TokenType.LESS_EQUAL:
                    left = left <= right
                elif op == TokenType.GREATER:
                    left = left > right
                elif op == TokenType.GREATER_EQUAL:
                    left = left >= right
            else:
                break
        return left
    
    def parse_add(self) -> Any:
        left = self.parse_mul()
        while True:
            token = self.peek()
            if token and token.type in [TokenType.PLUS, TokenType.MINUS]:
                op = self.consume().type
                right = self.parse_mul()
                if op == TokenType.PLUS:
                    left = left + right
                else:
                    left = left - right
            else:
                break
        return left
    
    def parse_mul(self) -> Any:
        left = self.parse_primary()
        while True:
            token = self.peek()
            if token and token.type in [TokenType.MULTIPLY, TokenType.DIVIDE]:
                op = self.consume().type
                right = self.parse_primary()
                if op == TokenType.MULTIPLY:
                    left = left * right
                else:
                    if right == 0:
                        raise ZeroDivisionError('Division by zero')
                    left = left / right
            else:
                break
        return left
    
    def parse_primary(self) -> Any:
        token = self.peek()
        if not token:
            raise SyntaxError('Unexpected end of expression')
        
        if token.type == TokenType.NUMBER:
            self.consume()
            return token.value
        elif token.type == TokenType.STRING:
            self.consume()
            return token.value
        elif token.type == TokenType.IDENTIFIER:
            self.consume()
            if token.value not in self.variables:
                raise NameError(f'Variable "{token.value}" is not defined')
            return self.variables[token.value]
        elif token.type == TokenType.LPAREN:
            self.consume()
            value = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return value
        elif token.type == TokenType.QUERY:
            return self.parse_query(return_value=True)
        else:
            raise SyntaxError(f'Unexpected token in expression: {token.type}')
    
    def parse_statement(self):
        """Парсит один оператор"""
        token = self.peek()
        if not token:
            return
        
        # Метки просто пропускаем
        if token.type == TokenType.LABEL:
            self.consume()
            return
        
        if token.type == TokenType.SAY:
            self.consume()
            value = self.parse_expression()
            self.consume(TokenType.SEMICOLON)
            print(value)
        
        elif token.type == TokenType.SET:
            self.parse_set()
        
        elif token.type == TokenType.OPEN:
            self.parse_open()
        
        elif token.type == TokenType.PING:
            self.parse_ping()
        
        elif token.type == TokenType.BROWSE:
            self.parse_browse()
        
        elif token.type == TokenType.LOOP:
            self.parse_loop()
        
        elif token.type == TokenType.CALL:
            self.parse_call()
        
        elif token.type == TokenType.RETURN:
            self.parse_return()
        
        elif token.type == TokenType.NDIR:
            self.parse_ndir()
        
        elif token.type == TokenType.DELETE:
            self.parse_delete()
        
        elif token.type == TokenType.QUERY:
            self.parse_query(return_value=False)
        
        elif token.type in [TokenType.INS, TokenType.INS_WR, TokenType.INS_CW]:
            mode = 'safe'
            if token.type == TokenType.INS_WR:
                mode = 'wr'
            elif token.type == TokenType.INS_CW:
                mode = 'cw'
            self.consume()
            self.parse_ins(mode)
        
        elif token.type == TokenType.DIR_S:
            self.parse_dir_s()
        
        elif token.type == TokenType.INP:
            self.parse_inp()
        
        else:
            raise SyntaxError(f'Unknown statement: {token.type}')
    
    def parse_set(self):
        """Команда set: set переменная = значение;"""
        self.consume(TokenType.SET)
        var_token = self.consume(TokenType.IDENTIFIER)
        var_name = var_token.value
        self.consume(TokenType.EQUALS)
        
        # Проверяем, не query ли это
        if self.peek().type == TokenType.QUERY:
            value = self.parse_query(return_value=True)
        else:
            value = self.parse_expression()
        
        self.consume(TokenType.SEMICOLON)
        self.variables[var_name] = value
    
    def parse_open(self):
        """Команда open: open "путь";"""
        self.consume(TokenType.OPEN)
        path_token = self.consume(TokenType.STRING)
        self.consume(TokenType.SEMICOLON)
        
        filepath = path_token.value
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tokens = lex(code)
            interpreter = Interpreter(tokens)
            interpreter.variables.update(self.variables)
            interpreter.run()
            self.variables.update(interpreter.variables)
            
        except FileNotFoundError:
            raise RuntimeError(f'File not found: {filepath}')
        except Exception as e:
            raise RuntimeError(f'Error executing file {filepath}: {e}')
    
    def parse_ping(self):
        """Команда ping: ping хост;"""
        self.consume(TokenType.PING)
        
        token = self.consume()
        if token.type == TokenType.STRING:
            host = token.value
        elif token.type == TokenType.IDENTIFIER:
            host = self.variables.get(token.value, token.value)
        else:
            raise SyntaxError('Expected hostname or IP address')
        
        self.consume(TokenType.SEMICOLON)
        
        system = platform.system().lower()
        
        try:
            if system == 'windows':
                cmd = ['ping', '-n', '1', '-w', '1000', host]
                output = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                match = re.search(r'время[=<](\d+)мс', output.stdout.lower())
                if match:
                    print(f"Ping {host}: {match.group(1)} ms")
                elif output.returncode == 0:
                    print(f"Ping {host}: OK")
                else:
                    print(f"Ping {host}: FAILED (no response)")
            else:
                cmd = ['ping', '-c', '1', '-W', '1', host]
                output = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                match = re.search(r'time[=<](\d+\.?\d*)\s*ms', output.stdout.lower())
                if match:
                    print(f"Ping {host}: {match.group(1)} ms")
                elif output.returncode == 0:
                    print(f"Ping {host}: OK")
                else:
                    print(f"Ping {host}: FAILED")
        except subprocess.TimeoutExpired:
            print(f"Ping {host}: TIMEOUT")
        except Exception as e:
            print(f"Ping {host}: ERROR - {str(e)}")
    
    def parse_browse(self):
        """Команда browse: browse сайт;"""
        self.consume(TokenType.BROWSE)
        
        token = self.consume()
        if token.type == TokenType.STRING:
            url = token.value
        elif token.type == TokenType.IDENTIFIER:
            url = self.variables.get(token.value, token.value)
        else:
            raise SyntaxError('Expected URL or variable')
        
        self.consume(TokenType.SEMICOLON)
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            webbrowser.open(url)
            print(f"Opening {url} in your browser...")
        except Exception as e:
            print(f"Error: Cannot open browser - {str(e)}")
    
    def parse_loop(self):
        """Команда loop: loop (условие) { тело }"""
        self.consume(TokenType.LOOP)
        self.consume(TokenType.LPAREN)
        
        # Сохраняем позицию условия
        cond_start = self.pos
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN)
        
        # Парсим тело
        body = self.parse_block()
        
        # Выполняем цикл
        max_iterations = 10000
        count = 0
        
        while count < max_iterations:
            # Вычисляем условие заново (перемещаемся обратно)
            old_pos = self.pos
            self.pos = cond_start
            cond_value = self.parse_expression()
            self.pos = old_pos
            
            if not cond_value:
                break
            
            # Выполняем тело
            old_vars = self.variables.copy()
            for stmt in body:
                self.execute_statement(stmt)
            
            count += 1
        
        if count >= max_iterations:
            print("Warning: Loop stopped after 10000 iterations")
    
    def parse_block(self) -> List[Token]:
        """Парсит блок кода в { ... } и возвращает токены блока"""
        self.consume(TokenType.LBRACE)
        start_pos = self.pos
        brace_count = 1
        
        while self.pos < len(self.tokens):
            if self.tokens[self.pos].type == TokenType.LBRACE:
                brace_count += 1
            elif self.tokens[self.pos].type == TokenType.RBRACE:
                brace_count -= 1
                if brace_count == 0:
                    break
            self.pos += 1
        
        block_tokens = self.tokens[start_pos:self.pos]
        self.consume(TokenType.RBRACE)
        return block_tokens
    
    def execute_statement(self, token):
        """Выполняет оператор из токена (для блоков)"""
        # Сохраняем позицию
        old_pos = self.pos
        # Временный интерпретатор для блока
        temp_interp = Interpreter([token])
        temp_interp.variables = self.variables.copy()
        temp_interp.run()
        self.variables.update(temp_interp.variables)
        self.pos = old_pos
    
    def parse_call(self):
        """Команда call: call имя(аргументы);"""
        self.consume(TokenType.CALL)
        label_token = self.consume(TokenType.IDENTIFIER)
        label_name = label_token.value
        
        # Парсим аргументы, если есть
        args = []
        if self.peek() and self.peek().type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            while self.peek() and self.peek().type != TokenType.RPAREN:
                args.append(self.parse_expression())
                if self.peek() and self.peek().type == TokenType.COMMA:
                    self.consume(TokenType.COMMA)
            self.consume(TokenType.RPAREN)
        
        self.consume(TokenType.SEMICOLON)
        
        if label_name not in self.labels:
            raise NameError(f'Label "{label_name}" not found')
        
        label_info = self.labels[label_name]
        
        if len(args) != len(label_info['params']):
            raise TypeError(f'Label {label_name} expects {len(label_info["params"])} arguments, got {len(args)}')
        
        # Сохраняем контекст
        self.call_stack.append({
            'pos': self.pos,
            'variables': self.variables.copy(),
            'return_value': None
        })
        
        # Создаём локальные переменные из параметров
        for param_name, arg_value in zip(label_info['params'], args):
            self.variables[param_name] = arg_value
        
        # Выполняем тело метки
        old_pos = self.pos
        self.pos = label_info['pos']
        
        while self.pos < label_info['body_end']:
            if self.peek() and self.peek().type == TokenType.RETURN:
                self.parse_return()
                break
            self.parse_statement()
        
        result = self.call_stack.pop()['return_value']
        self.variables = self.call_stack[-1]['variables'] if self.call_stack else self.variables
        self.pos = self.call_stack[-1]['pos'] if self.call_stack else old_pos
        
        if result is not None:
            return result
    
    def parse_return(self):
        """Команда return: return значение;"""
        self.consume(TokenType.RETURN)
        
        value = None
        if self.peek() and self.peek().type != TokenType.SEMICOLON:
            value = self.parse_expression()
        
        self.consume(TokenType.SEMICOLON)
        
        if not self.call_stack:
            raise RuntimeError('Return outside of call')
        
        self.call_stack[-1]['return_value'] = value
    
    def parse_ndir(self):
        """Команда ndir: ndir "путь";"""
        self.consume(TokenType.NDIR)
        
        token = self.consume()
        if token.type == TokenType.STRING:
            path = token.value
        elif token.type == TokenType.IDENTIFIER:
            path = self.variables.get(token.value, token.value)
        else:
            raise SyntaxError('Expected folder path')
        
        self.consume(TokenType.SEMICOLON)
        
        try:
            os.makedirs(path, exist_ok=True)
            print(f"Created directory: {path}")
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
    
    def parse_delete(self):
        """Команда del: del "путь" [-r];"""
        self.consume(TokenType.DELETE)
        
        token = self.consume()
        if token.type == TokenType.STRING:
            path = token.value
        elif token.type == TokenType.IDENTIFIER:
            path = self.variables.get(token.value, token.value)
        else:
            raise SyntaxError('Expected file or folder path')
        
        recursive = False
        if self.peek() and self.peek().type == TokenType.IDENTIFIER and self.peek().value == '-r':
            self.consume()
            recursive = True
        
        self.consume(TokenType.SEMICOLON)
        
        try:
            if os.path.isfile(path):
                os.remove(path)
                print(f"Deleted file: {path}")
            elif os.path.isdir(path):
                if recursive:
                    shutil.rmtree(path)
                    print(f"Deleted directory (recursive): {path}")
                else:
                    print(f"Error: '{path}' is a directory. Use 'del {path} -r;' to delete directories")
            else:
                print(f"Error: '{path}' not found")
        except Exception as e:
            print(f"Error deleting {path}: {e}")
    
    def parse_query(self, return_value=False):
        """Команда query: query "путь"; или set x = query "путь";"""
        self.consume(TokenType.QUERY)
        
        token = self.peek()
        if token.type == TokenType.STRING:
            self.consume()
            path = token.value
        elif token.type == TokenType.IDENTIFIER:
            self.consume()
            path = self.variables.get(token.value, token.value)
        else:
            raise SyntaxError('Expected file path')
        
        if not return_value:
            self.consume(TokenType.SEMICOLON)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not return_value:
                print(content)
            return content
        except FileNotFoundError:
            error_msg = f"Error: File '{path}' not found"
            if return_value:
                return None
            else:
                print(error_msg)
        except Exception as e:
            error_msg = f"Error reading file '{path}': {e}"
            if return_value:
                return None
            else:
                print(error_msg)
    
    def parse_ins(self, mode='safe'):
        """Команда ins: ins "путь" "содержимое"; / ins wr / ins cw"""
        # Получаем путь к файлу
        path_token = self.peek()
        if path_token.type == TokenType.STRING:
            self.consume()
            path = path_token.value
        elif path_token.type == TokenType.IDENTIFIER:
            self.consume()
            path = self.variables.get(path_token.value, path_token.value)
        else:
            raise SyntaxError('Expected file path')
        
        # Получаем содержимое
        content_token = self.peek()
        content = None
        
        if content_token.type == TokenType.STRING:
            self.consume()
            content = content_token.value
        elif content_token.type == TokenType.IDENTIFIER:
            self.consume()
            content = self.variables.get(content_token.value, content_token.value)
        elif content_token.type == TokenType.NUMBER:
            self.consume()
            content = str(content_token.value)
        else:
            raise SyntaxError('Expected content')
        
        self.consume(TokenType.SEMICOLON)
        
        # Для режимов wr и cw — проверяем существование файла
        if mode in ['wr', 'cw'] and not os.path.exists(path):
            print(f"Error: File '{path}' does not exist. Use 'ins' to create a new file.")
            return
        
        # Режим safe: проверяем что файла нет
        if mode == 'safe' and os.path.exists(path):
            print(f"Error: File '{path}' already exists. Use 'ins cw' to overwrite or 'ins wr' to append")
            return
        
        try:
            # Создаём папки, если их нет
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Записываем в зависимости от режима
            if mode == 'wr':  # append
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(str(content))
                print(f"Appended to file: {path}")
            else:  # safe или cw (overwrite)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
                print(f"File written: {path}")
                
        except Exception as e:
            print(f"Error writing to file '{path}': {e}")
    
    def parse_dir_s(self):
        """Команда dir /s: dir /s "путь" "маска";"""
        self.consume(TokenType.DIR_S)
        
        # Получаем путь для поиска
        path_token = self.peek()
        if path_token.type == TokenType.STRING:
            self.consume()
            search_path = path_token.value
        elif path_token.type == TokenType.IDENTIFIER:
            self.consume()
            search_path = self.variables.get(path_token.value, path_token.value)
        else:
            raise SyntaxError('Expected search path')
        
        # Получаем маску для поиска
        mask_token = self.peek()
        if mask_token.type == TokenType.STRING:
            self.consume()
            mask = mask_token.value
        elif mask_token.type == TokenType.IDENTIFIER:
            self.consume()
            mask = self.variables.get(mask_token.value, mask_token.value)
        else:
            raise SyntaxError('Expected search mask (e.g., "*.txt")')
        
        self.consume(TokenType.SEMICOLON)
        
        # Проверяем существование папки
        if not os.path.exists(search_path):
            self.variables['dir_s_'] = 0
            self.variables['dir_s_p_'] = ""
            return
        
        # Поиск файлов по маске
        found_files = []
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if fnmatch.fnmatch(file, mask):
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
        except Exception as e:
            self.variables['dir_s_'] = 0
            self.variables['dir_s_p_'] = ""
            return
        
        # Сохраняем результаты
        if found_files:
            self.variables['dir_s_'] = 1
            self.variables['dir_s_p_'] = '|'.join(found_files)
        else:
            self.variables['dir_s_'] = 0
            self.variables['dir_s_p_'] = ""
    
    def parse_inp(self):
        """Команда inp: inp "переменная" = "текст запроса";"""
        self.consume(TokenType.INP)
        
        # Получаем имя переменной
        var_token = self.consume(TokenType.STRING)
        var_name = var_token.value
        
        # Проверяем знак =
        self.consume(TokenType.EQUALS)
        
        # Получаем текст запроса
        prompt_token = self.consume(TokenType.STRING)
        prompt = prompt_token.value
        
        self.consume(TokenType.SEMICOLON)
        
        # Запрашиваем ввод
        user_input = input(prompt)
        
        # Пробуем преобразовать в число, если получается
        try:
            if '.' in user_input:
                self.variables[var_name] = float(user_input)
            else:
                self.variables[var_name] = int(user_input)
        except ValueError:
            self.variables[var_name] = user_input
    
    def run(self):
        """Запускает выполнение всех операторов"""
        while self.pos < len(self.tokens):
            self.parse_statement()

# ----- REPL -----
def repl():
    print("XCode 1.0 new programming language, Damirus Papirus (All rights reserved)")
    
    while True:
        try:
            code = input('\n>>> ')
            if code.strip().lower() == 'exit':
                break
            if not code.strip():
                continue
            
            tokens = lex(code)
            interpreter = Interpreter(tokens)
            interpreter.run()
            
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f'Error: {e}')

if __name__ == '__main__':
    repl()