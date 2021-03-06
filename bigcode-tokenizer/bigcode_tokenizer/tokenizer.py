from typing import List, Tuple, Dict, Type
from os import path

from bigcode_tokenizer.token import Token

from pygments.lexers.jvm import JavaLexer
from pygments.lexers.python import PythonLexer, Python3Lexer
from pygments import token


RawToken = Tuple[token._TokenType, str]


class Tokenizer:
    def __init__(self, include_values: bool = True, skip_text: bool = True,
                 skip_comments: bool = True, max_len: int = 50000) -> None:
        self.include_values = include_values
        self.skip_text = skip_text
        self.skip_comments = skip_comments
        self.max_len = max_len

    @property
    def lexer(self):
        if not hasattr(self, "_lexer"):
            raise NotImplementedError()
        return getattr(self, "_lexer")

    def _should_skip(self, tok: RawToken) -> bool:
        if self.skip_text and tok[0] in token.Text:
            return True
        if self.skip_comments and tok[0] in token.Comment:
            return True
        return False

    def skip_tokens(self, raw_tokens: List[RawToken]) -> Tuple[List[RawToken], int]:
        skipped = 0
        while len(raw_tokens) > skipped and self._should_skip(raw_tokens[skipped]):
            skipped += 1
        return raw_tokens[skipped:], skipped

    def transform_raw_token(self, raw_token: RawToken) -> Token:
        token_type, token_value = raw_token
        token_type = str(token_type).replace("Token.", "")
        if not self.include_values:
            token_value = None
        return Token(token_type, token_value)

    def get_next_token(self, raw_tokens: List[RawToken]) -> Tuple[Token, int]:
        return self.transform_raw_token(raw_tokens[0]), 1

    def tokenize_string(self, code: str) -> List[Token]:
        raw_tokens = list(self.lexer.get_tokens(code))
        tokens = []
        while raw_tokens:
            raw_tokens, consumed_count = self.skip_tokens(raw_tokens)
            new_token = None
            if raw_tokens:
                new_token, read_count = self.get_next_token(raw_tokens)
                consumed_count += read_count
            if new_token:
                tokens.append(new_token)
            raw_tokens = raw_tokens[consumed_count:]
        return tokens

    def tokenize_file(self, filename: str) -> List[Token]:
        with open(filename) as f:
            content = f.read()
            if len(content) > self.max_len:
                return None
            return self.tokenize_string(content)


class JavaTokenizer(Tokenizer):
    MULTI_CHARS_OPS = [
        (4, [">>>="]),
        (3, [">>=", "<<=", ">>>"]),
        (2, ["==", "!=", ">=", "<=", "+=", "-=", "*=", "/=", "%=", "&=",
             "^=", "|=", ">>", "<<", "++", "--", "&&", "||"])
    ]

    def __init__(self, **kwargs):
        super(JavaTokenizer, self).__init__(**kwargs)
        self._lexer = JavaLexer()

    def get_next_token(self, raw_tokens: List[RawToken]) -> Tuple[Token, int]:
        # handle operators with multiple chars
        for chars_count, operators in self.MULTI_CHARS_OPS:
            if len(raw_tokens) <= chars_count:
                continue
            if not all(v[0] == token.Operator for v in raw_tokens[:chars_count]):
                continue
            value = "".join(v[1] for v in raw_tokens[:chars_count])
            if value in operators:
                return self.transform_raw_token((token.Operator, value)), chars_count

        return super(JavaTokenizer, self).get_next_token(raw_tokens)


class PythonTokenizer(Tokenizer):
    pass


class Python3Tokenizer(PythonTokenizer):
    def __init__(self, **kwargs):
        super(Python3Tokenizer, self).__init__(**kwargs)
        self._lexer = Python3Lexer()


class Python2Tokenizer(PythonTokenizer):
    def __init__(self, **kwargs):
        super(Python2Tokenizer, self).__init__(**kwargs)
        self._lexer = PythonLexer()


TOKENIZERS: Dict[str, Type[Tokenizer]] = {
    "java": JavaTokenizer,
    "py": Python3Tokenizer,
    "python": Python3Tokenizer,
    "python2": PythonTokenizer,
}


def tokenize_file(filename: str, options: dict) -> List[Token]:
    tokenizer_name = options.pop("tokenizer", None) or path.splitext(filename)[1][1:]
    if tokenizer_name not in TOKENIZERS:
        raise ValueError("no tokenizer named {0} found for {1}".format(tokenizer_name, filename))
    tokenizer = TOKENIZERS[tokenizer_name](**options)
    return tokenizer.tokenize_file(filename)
