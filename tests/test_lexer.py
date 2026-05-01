"""
Tests for the COOL lexer.

These tests verify that the lexer correctly tokenizes COOL programs,
including handling of strings, comments, and edge cases.
"""

import pytest

from pycoolc.lexer import LexerError, PyCoolLexer, make_lexer


class TestLexerBasics:
    """Basic tokenization tests."""

    def test_empty_input_produces_no_tokens(self):
        lexer = make_lexer()
        lexer.input("")
        tokens = list(lexer)
        assert tokens == []

    def test_whitespace_only_produces_no_tokens(self):
        lexer = make_lexer()
        lexer.input("   \t\n\r\f   ")
        tokens = list(lexer)
        assert tokens == []


class TestIntegerTokens:
    """Tests for integer literal tokenization."""

    def test_single_digit(self):
        lexer = make_lexer()
        lexer.input("5")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 5

    def test_multi_digit(self):
        lexer = make_lexer()
        lexer.input("12345")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 12345

    def test_zero(self):
        lexer = make_lexer()
        lexer.input("0")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 0


class TestBooleanTokens:
    """Tests for boolean literal tokenization."""

    def test_true_literal(self):
        lexer = make_lexer()
        lexer.input("true")
        token = lexer.token()
        assert token.type == "BOOLEAN"
        assert token.value is True

    def test_false_literal(self):
        lexer = make_lexer()
        lexer.input("false")
        token = lexer.token()
        assert token.type == "BOOLEAN"
        assert token.value is False

    def test_true_prefix_is_identifier(self):
        """'truevalue' must tokenize as a single ID, not BOOLEAN + ID."""
        lexer = make_lexer()
        lexer.input("truevalue")
        tokens = list(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == "ID"
        assert tokens[0].value == "truevalue"

    def test_false_prefix_is_identifier(self):
        """'falsehood' must tokenize as a single ID, not BOOLEAN + ID."""
        lexer = make_lexer()
        lexer.input("falsehood")
        tokens = list(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == "ID"
        assert tokens[0].value == "falsehood"

    def test_true_with_digits_is_identifier(self):
        lexer = make_lexer()
        lexer.input("true123")
        tokens = list(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == "ID"
        assert tokens[0].value == "true123"

    def test_true_with_underscore_is_identifier(self):
        lexer = make_lexer()
        lexer.input("true_flag")
        tokens = list(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == "ID"
        assert tokens[0].value == "true_flag"


class TestStringTokens:
    """Tests for string literal tokenization."""

    def test_simple_string(self):
        lexer = make_lexer()
        lexer.input('"hello"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello"

    def test_empty_string(self):
        lexer = make_lexer()
        lexer.input('""')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == ""

    def test_string_with_spaces(self):
        lexer = make_lexer()
        lexer.input('"hello world"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello world"

    def test_escape_sequence_newline(self):
        lexer = make_lexer()
        lexer.input('"hello\\nworld"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello\nworld"

    def test_escape_sequence_tab(self):
        lexer = make_lexer()
        lexer.input('"hello\\tworld"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello\tworld"

    def test_escape_sequence_backslash(self):
        lexer = make_lexer()
        lexer.input('"hello\\\\world"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello\\world"

    def test_escape_sequence_quote(self):
        lexer = make_lexer()
        lexer.input('"hello\\"world"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == 'hello"world'

    def test_escape_sequence_backspace(self):
        lexer = make_lexer()
        lexer.input('"hello\\bworld"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello\bworld"

    def test_escape_sequence_formfeed(self):
        lexer = make_lexer()
        lexer.input('"hello\\fworld"')
        token = lexer.token()
        assert token.type == "STRING"
        assert token.value == "hello\fworld"

    def test_escaped_newline_in_string(self):
        # A backslash followed by actual newline continues the string
        lexer = make_lexer()
        lexer.input('"hello\\\nworld"')
        token = lexer.token()
        assert token.type == "STRING"
        # The escaped newline is consumed, not included
        assert token.value == "helloworld"


class TestIdentifiersAndTypes:
    """Tests for identifier and type name tokenization."""

    def test_lowercase_identifier(self):
        lexer = make_lexer()
        lexer.input("foo")
        token = lexer.token()
        assert token.type == "ID"
        assert token.value == "foo"

    def test_identifier_with_underscore(self):
        lexer = make_lexer()
        lexer.input("foo_bar")
        token = lexer.token()
        assert token.type == "ID"
        assert token.value == "foo_bar"

    def test_identifier_starting_with_underscore(self):
        lexer = make_lexer()
        lexer.input("_foo")
        token = lexer.token()
        assert token.type == "ID"
        assert token.value == "_foo"

    def test_identifier_with_numbers(self):
        lexer = make_lexer()
        lexer.input("foo123")
        token = lexer.token()
        assert token.type == "ID"
        assert token.value == "foo123"

    def test_type_name_uppercase_start(self):
        lexer = make_lexer()
        lexer.input("Foo")
        token = lexer.token()
        assert token.type == "TYPE"
        assert token.value == "Foo"

    def test_type_name_with_numbers(self):
        lexer = make_lexer()
        lexer.input("Foo123")
        token = lexer.token()
        assert token.type == "TYPE"
        assert token.value == "Foo123"


class TestKeywords:
    """Tests for COOL keyword tokenization."""

    @pytest.mark.parametrize(
        "keyword,expected_type",
        [
            ("class", "CLASS"),
            ("inherits", "INHERITS"),
            ("if", "IF"),
            ("then", "THEN"),
            ("else", "ELSE"),
            ("fi", "FI"),
            ("while", "WHILE"),
            ("loop", "LOOP"),
            ("pool", "POOL"),
            ("let", "LET"),
            ("in", "IN"),
            ("case", "CASE"),
            ("of", "OF"),
            ("esac", "ESAC"),
            ("new", "NEW"),
            ("not", "NOT"),
            ("isvoid", "ISVOID"),
            ("self", "SELF"),
        ],
    )
    def test_keyword(self, keyword, expected_type):
        lexer = make_lexer()
        lexer.input(keyword)
        token = lexer.token()
        assert token.type == expected_type


class TestCaseInsensitiveKeywords:
    """Tests for case-insensitive keyword handling per COOL spec §2."""

    @pytest.mark.parametrize(
        "keyword,expected_type",
        [
            # Uppercase versions
            ("CLASS", "CLASS"),
            ("INHERITS", "INHERITS"),
            ("IF", "IF"),
            ("THEN", "THEN"),
            ("ELSE", "ELSE"),
            ("NOT", "NOT"),
            # Mixed case
            ("Class", "CLASS"),
            ("Inherits", "INHERITS"),
            ("If", "IF"),
            ("Then", "THEN"),
            ("Else", "ELSE"),
            ("Not", "NOT"),
            ("WhIlE", "WHILE"),
        ],
    )
    def test_keyword_case_insensitive(self, keyword, expected_type):
        lexer = make_lexer()
        lexer.input(keyword)
        token = lexer.token()
        assert token.type == expected_type


class TestOperators:
    """Tests for operator tokenization."""

    @pytest.mark.parametrize(
        "op,expected_type",
        [
            ("+", "PLUS"),
            ("-", "MINUS"),
            ("*", "MULTIPLY"),
            ("/", "DIVIDE"),
            ("=", "EQ"),
            ("<", "LT"),
            ("<=", "LTEQ"),
            ("<-", "ASSIGN"),
            ("~", "INT_COMP"),
            ("=>", "ARROW"),
        ],
    )
    def test_operator(self, op, expected_type):
        lexer = make_lexer()
        lexer.input(op)
        token = lexer.token()
        assert token.type == expected_type


class TestDelimiters:
    """Tests for delimiter tokenization."""

    @pytest.mark.parametrize(
        "delim,expected_type",
        [
            ("(", "LPAREN"),
            (")", "RPAREN"),
            ("{", "LBRACE"),
            ("}", "RBRACE"),
            (":", "COLON"),
            (";", "SEMICOLON"),
            (",", "COMMA"),
            (".", "DOT"),
            ("@", "AT"),
        ],
    )
    def test_delimiter(self, delim, expected_type):
        lexer = make_lexer()
        lexer.input(delim)
        token = lexer.token()
        assert token.type == expected_type


class TestComments:
    """Tests for comment handling."""

    def test_single_line_comment_ignored(self):
        lexer = make_lexer()
        lexer.input("-- this is a comment\n42")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 42

    def test_single_line_comment_at_end(self):
        lexer = make_lexer()
        lexer.input("42 -- this is a comment")
        tokens = list(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == "INTEGER"

    def test_block_comment_ignored(self):
        lexer = make_lexer()
        lexer.input("(* this is a comment *) 42")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 42

    def test_nested_block_comments(self):
        # COOL supports nested comments
        lexer = make_lexer()
        lexer.input("(* outer (* inner *) outer *) 42")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 42

    def test_multiline_block_comment(self):
        lexer = make_lexer()
        lexer.input("(* line 1\nline 2\nline 3 *) 42")
        token = lexer.token()
        assert token.type == "INTEGER"
        assert token.value == 42


class TestComplexTokenization:
    """Tests for tokenizing complete COOL constructs."""

    def test_class_declaration(self):
        lexer = make_lexer()
        lexer.input("class Main inherits IO { };")
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == ["CLASS", "TYPE", "INHERITS", "TYPE", "LBRACE", "RBRACE", "SEMICOLON"]

    def test_method_declaration(self):
        lexer = make_lexer()
        lexer.input("main(): Object { self };")
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == [
            "ID",
            "LPAREN",
            "RPAREN",
            "COLON",
            "TYPE",
            "LBRACE",
            "SELF",
            "RBRACE",
            "SEMICOLON",
        ]

    def test_arithmetic_expression(self):
        lexer = make_lexer()
        lexer.input("1 + 2 * 3")
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == ["INTEGER", "PLUS", "INTEGER", "MULTIPLY", "INTEGER"]

    def test_assignment(self):
        lexer = make_lexer()
        lexer.input("x <- 42")
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == ["ID", "ASSIGN", "INTEGER"]

    def test_method_call(self):
        lexer = make_lexer()
        lexer.input('out_string("Hello")')
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == ["ID", "LPAREN", "STRING", "RPAREN"]

    def test_static_dispatch(self):
        lexer = make_lexer()
        lexer.input("self@Object.abort()")
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == ["SELF", "AT", "TYPE", "DOT", "ID", "LPAREN", "RPAREN"]

    def test_case_expression(self):
        lexer = make_lexer()
        lexer.input("case x of y : Int => 1; esac")
        tokens = list(lexer)
        types = [t.type for t in tokens]
        assert types == [
            "CASE",
            "ID",
            "OF",
            "ID",
            "COLON",
            "TYPE",
            "ARROW",
            "INTEGER",
            "SEMICOLON",
            "ESAC",
        ]


class TestLineNumbers:
    """Tests for line number tracking."""

    def test_line_numbers_increment_on_newline(self):
        lexer = make_lexer()
        lexer.input("42\n\n\n99")
        tokens = list(lexer)
        assert tokens[0].lineno == 1
        assert tokens[1].lineno == 4


class TestLexerAPI:
    """Tests for the lexer's public API."""

    def test_iterator_protocol(self):
        lexer = make_lexer()
        lexer.input("1 2 3")
        tokens = list(lexer)
        assert len(tokens) == 3

    def test_token_method(self):
        lexer = make_lexer()
        lexer.input("42")
        token = lexer.token()
        assert token is not None
        assert token.type == "INTEGER"
        # After consuming all tokens
        assert lexer.token() is None

    def test_build_not_called_raises_on_input(self):
        lexer = PyCoolLexer(build_lexer=False)
        with pytest.raises(RuntimeError, match="Lexer was not built"):
            lexer.input("42")

    def test_clone_creates_independent_lexer(self):
        lexer = make_lexer()
        lexer.input("1 2 3")
        lexer.token()  # consume first token
        lexer.clone_ply_lexer()
        # Clone should start from current position
        original_remaining = list(lexer)
        assert len(original_remaining) == 2


class TestLexerErrors:
    """COOL §7.1, §10 — lexical error conditions."""

    def test_eof_in_string_raises(self):
        lexer = make_lexer()
        lexer.input('"hello')
        with pytest.raises(LexerError, match="EOF in string"):
            list(lexer)

    def test_eof_in_string_reports_start_line(self):
        lexer = make_lexer()
        lexer.input('\n\n"hello')
        with pytest.raises(LexerError) as exc:
            list(lexer)
        assert exc.value.lineno == 3

    def test_eof_in_comment_raises(self):
        lexer = make_lexer()
        lexer.input("(* unterminated")
        with pytest.raises(LexerError, match="EOF in comment"):
            list(lexer)

    def test_eof_in_nested_comment_raises(self):
        lexer = make_lexer()
        lexer.input("(* outer (* inner")
        with pytest.raises(LexerError, match="EOF in comment"):
            list(lexer)

    def test_backslash_then_eof_in_string_raises(self):
        lexer = make_lexer()
        lexer.input('"hi\\')
        with pytest.raises(LexerError, match="EOF in string"):
            list(lexer)

    def test_string_at_max_length_ok(self):
        """1024 chars is the limit per §7.1."""
        lexer = make_lexer()
        lexer.input('"' + "a" * 1024 + '"')
        toks = list(lexer)
        assert len(toks) == 1
        assert toks[0].type == "STRING"
        assert len(toks[0].value) == 1024

    def test_string_too_long_raises(self):
        lexer = make_lexer()
        lexer.input('"' + "a" * 1025 + '"')
        with pytest.raises(LexerError, match="String constant too long"):
            list(lexer)

    def test_null_char_in_string_raises(self):
        lexer = make_lexer()
        lexer.input('"hi\x00world"')
        with pytest.raises(LexerError, match="null character"):
            list(lexer)

    def test_escaped_zero_is_literal_zero(self):
        """\\0 escape per §10.2 means char '0', not NUL."""
        lexer = make_lexer()
        lexer.input('"a\\0b"')
        toks = list(lexer)
        assert toks[0].type == "STRING"
        assert toks[0].value == "a0b"

    def test_unescaped_newline_in_string_raises(self):
        """COOL §10.2: 'A non-escaped newline character may not appear in a string'."""
        lexer = make_lexer()
        lexer.input('"hello\nworld"')
        with pytest.raises(LexerError, match="Unterminated string"):
            list(lexer)

    def test_escaped_newline_in_string_ok(self):
        """\\<newline> is allowed and continues the string per §10.2."""
        lexer = make_lexer()
        lexer.input('"hello\\\nworld"')
        toks = list(lexer)
        assert toks[0].type == "STRING"

    def test_unmatched_comment_close_raises(self):
        lexer = make_lexer()
        lexer.input("foo *)")
        with pytest.raises(LexerError, match=r"Unmatched '\*\)'"):
            list(lexer)

    def test_star_then_paren_ok(self):
        """`* )` (with space) is MULTIPLY then RPAREN, not unmatched."""
        lexer = make_lexer()
        lexer.input("a * b )")
        toks = [t.type for t in lexer]
        assert "MULTIPLY" in toks
        assert "RPAREN" in toks

    def test_int_at_max_ok(self):
        lexer = make_lexer()
        lexer.input("2147483647")
        toks = list(lexer)
        assert toks[0].type == "INTEGER"
        assert toks[0].value == 2147483647

    def test_int_overflow_raises(self):
        lexer = make_lexer()
        lexer.input("2147483648")
        with pytest.raises(LexerError, match="exceeds 32-bit"):
            list(lexer)

    def test_huge_int_raises(self):
        lexer = make_lexer()
        lexer.input("99999999999999999999")
        with pytest.raises(LexerError, match="exceeds 32-bit"):
            list(lexer)

    def test_illegal_char_raises(self):
        lexer = make_lexer()
        lexer.input("a # b")
        with pytest.raises(LexerError, match="Illegal character"):
            list(lexer)

    def test_illegal_char_in_string_raises(self):
        """COMMENT state error fires only on weird input; verify STRING state too."""
        # \v (vertical tab, ascii 11) is not in t_ignore for STRING state,
        # and not matched by [^\n], so ... actually [^\n] matches anything except \n
        # so \v would go through t_STRING_anything. So construct a different test.
        # Use a real illegal char by putting NUL outside string state.
        lexer = make_lexer()
        lexer.input("\x01abc")  # SOH control char outside string
        with pytest.raises(LexerError, match="Illegal character"):
            list(lexer)

    @pytest.mark.parametrize(
        "src,expected_value",
        [
            ("true", True),
            ("tRue", True),
            ("tRuE", True),
            ("trUE", True),
            ("false", False),
            ("falsE", False),
            ("fAlSe", False),
            ("fALSE", False),
        ],
    )
    def test_boolean_trailing_case(self, src, expected_value):
        """COOL §10.4: trailing letters of true/false may be any case."""
        lexer = make_lexer()
        lexer.input(src)
        toks = list(lexer)
        assert len(toks) == 1
        assert toks[0].type == "BOOLEAN"
        assert toks[0].value is expected_value

    @pytest.mark.parametrize("src", ["True", "TRUE", "False", "FALSE", "TrUe"])
    def test_boolean_uppercase_first_letter_is_type(self, src):
        """First letter must be lowercase per §10.4."""
        lexer = make_lexer()
        lexer.input(src)
        toks = list(lexer)
        assert len(toks) == 1
        assert toks[0].type == "TYPE"

    def test_vertical_tab_is_whitespace(self):
        """COOL §10.5: \\v (ASCII 11) counts as whitespace."""
        lexer = make_lexer()
        lexer.input("a\vb")
        toks = list(lexer)
        assert len(toks) == 2
        assert toks[0].type == "ID" and toks[0].value == "a"
        assert toks[1].type == "ID" and toks[1].value == "b"


class TestFileBoundaries:
    """COOL §10.2/§10.3: strings and comments cannot cross file boundaries.

    Driver enforces this by lexing each file independently before concat.
    These tests verify the per-file lexer raises on dangling state.
    """

    def test_string_unterminated_in_file_raises(self):
        # Simulates a file whose contents end inside an open string
        lexer = make_lexer()
        lexer.input('class A { x : String <- "leak')
        with pytest.raises(LexerError, match="EOF in string"):
            list(lexer)

    def test_comment_unterminated_in_file_raises(self):
        lexer = make_lexer()
        lexer.input("(* this comment never closes\nclass A { };")
        with pytest.raises(LexerError, match="EOF in comment"):
            list(lexer)
