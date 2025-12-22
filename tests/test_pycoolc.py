"""
Tests for the compiler driver (pycoolc.py).
"""

import pytest
import sys
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from pycoolc.pycoolc import (
    create_arg_parser,
    lexical_analysis,
    syntax_analysis,
    semantic_analysis,
    code_generation,
    compile_program,
    main,
)


class TestArgParser:
    """Tests for command-line argument parsing."""

    def test_single_input_file(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl"])
        assert args.cool_program == ["test.cl"]

    def test_multiple_input_files(self):
        parser = create_arg_parser()
        args = parser.parse_args(["a.cl", "b.cl", "c.cl"])
        assert args.cool_program == ["a.cl", "b.cl", "c.cl"]

    def test_output_file_short(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl", "-o", "out.s"])
        assert args.outfile == "out.s"

    def test_output_file_long(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl", "--outfile", "out.s"])
        assert args.outfile == "out.s"

    def test_tokens_flag(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl", "--tokens"])
        assert args.tokens is True

    def test_ast_flag(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl", "--ast"])
        assert args.ast is True

    def test_semantics_flag(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl", "--semantics"])
        assert args.semantics is True

    def test_no_codegen_flag(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl", "--no-codegen"])
        assert args.no_codegen is True

    def test_default_values(self):
        parser = create_arg_parser()
        args = parser.parse_args(["test.cl"])
        assert args.outfile is None
        assert args.tokens is False
        assert args.ast is False
        assert args.semantics is False
        assert args.no_codegen is False


class TestLexicalAnalysis:
    """Tests for the lexical analysis phase."""

    def test_returns_token_list(self):
        tokens = lexical_analysis("class Main { };", print_results=False)
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_tokenizes_keywords(self):
        tokens = lexical_analysis("class if then else fi", print_results=False)
        token_types = [t.type for t in tokens]
        assert "CLASS" in token_types
        assert "IF" in token_types
        assert "THEN" in token_types
        assert "ELSE" in token_types
        assert "FI" in token_types

    def test_prints_tokens_when_enabled(self, capsys):
        lexical_analysis("class Main { };", print_results=True)
        captured = capsys.readouterr()
        assert "CLASS" in captured.out


class TestSyntaxAnalysis:
    """Tests for the syntax analysis phase."""

    def test_returns_ast(self):
        ast = syntax_analysis("class Main { };", print_results=False)
        assert ast is not None
        assert hasattr(ast, "classes")

    def test_parses_class(self):
        ast = syntax_analysis("class Main { };", print_results=False)
        assert len(ast.classes) == 1
        assert ast.classes[0].name == "Main"

    def test_prints_ast_when_enabled(self, capsys):
        syntax_analysis("class Main { };", print_results=True)
        captured = capsys.readouterr()
        assert "Program" in captured.out or "Main" in captured.out


class TestSemanticAnalysis:
    """Tests for the semantic analysis phase."""

    def test_returns_analyzed_ast_and_analyzer(self):
        from pycoolc.parser import make_parser
        parser = make_parser()
        ast = parser.parse("class Main { main(): Object { self }; };")
        result, analyzer = semantic_analysis(ast, print_results=False)
        assert result is not None
        assert analyzer is not None

    def test_analyzer_has_class_info(self):
        from pycoolc.parser import make_parser
        parser = make_parser()
        ast = parser.parse("class Main { main(): Object { self }; };")
        _, analyzer = semantic_analysis(ast, print_results=False)
        # Check that analyzer has processed the Main class
        assert "Main" in analyzer._classes_map


class TestCodeGeneration:
    """Tests for the code generation phase."""

    def test_generates_mips_code(self):
        from pycoolc.parser import make_parser
        from pycoolc.semanalyser import make_semantic_analyser
        
        parser = make_parser()
        ast = parser.parse("class Main { main(): Object { self }; };")
        analyzer = make_semantic_analyser()
        analyzed = analyzer.transform(ast)
        
        code = code_generation(analyzed, analyzer, output_file=None)
        assert ".data" in code
        assert ".text" in code

    def test_writes_to_output_file(self, tmp_path):
        from pycoolc.parser import make_parser
        from pycoolc.semanalyser import make_semantic_analyser
        
        parser = make_parser()
        ast = parser.parse("class Main { main(): Object { self }; };")
        analyzer = make_semantic_analyser()
        analyzed = analyzer.transform(ast)
        
        output_file = tmp_path / "test.s"
        code_generation(analyzed, analyzer, output_file=str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text()
        assert ".data" in content


class TestCompileProgram:
    """Tests for the main compile_program function."""

    def test_compiles_simple_program(self):
        code = compile_program(
            "class Main { main(): Object { self }; };",
            output_file=None,
        )
        assert code is not None
        assert ".data" in code
        assert ".text" in code

    def test_skip_codegen_returns_none(self):
        result = compile_program(
            "class Main { main(): Object { self }; };",
            skip_codegen=True,
        )
        assert result is None

    def test_print_tokens_outputs_to_stdout(self, capsys):
        compile_program(
            "class Main { main(): Object { self }; };",
            print_tokens=True,
        )
        captured = capsys.readouterr()
        assert "Lexical Analysis" in captured.out

    def test_print_ast_outputs_to_stdout(self, capsys):
        compile_program(
            "class Main { main(): Object { self }; };",
            print_ast=True,
        )
        captured = capsys.readouterr()
        assert "Syntax Analysis" in captured.out

    def test_print_semantics_outputs_to_stdout(self, capsys):
        compile_program(
            "class Main { main(): Object { self }; };",
            print_semantics=True,
        )
        captured = capsys.readouterr()
        assert "Semantic Analysis" in captured.out

    def test_writes_to_output_file(self, tmp_path):
        output_file = tmp_path / "test.s"
        compile_program(
            "class Main { main(): Object { self }; };",
            output_file=str(output_file),
        )
        assert output_file.exists()

    def test_invalid_syntax_returns_none(self):
        result = compile_program("class { invalid syntax")
        assert result is None


class TestMain:
    """Tests for the main entry point."""

    def test_missing_file_returns_error(self, tmp_path):
        with patch.object(sys, "argv", ["pycoolc", str(tmp_path / "nonexistent.cl")]):
            result = main()
        assert result == 1

    def test_invalid_extension_returns_error(self, tmp_path):
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("class Main { };")
        with patch.object(sys, "argv", ["pycoolc", str(bad_file)]):
            result = main()
        assert result == 1

    def test_successful_compilation_returns_zero(self, tmp_path):
        source_file = tmp_path / "test.cl"
        source_file.write_text("class Main { main(): Object { self }; };")
        output_file = tmp_path / "test.s"
        
        with patch.object(sys, "argv", ["pycoolc", str(source_file), "-o", str(output_file)]):
            result = main()
        
        assert result == 0
        assert output_file.exists()

    def test_no_codegen_flag_skips_output(self, tmp_path):
        source_file = tmp_path / "test.cl"
        source_file.write_text("class Main { main(): Object { self }; };")
        
        with patch.object(sys, "argv", ["pycoolc", str(source_file), "--no-codegen"]):
            result = main()
        
        assert result == 0

    def test_multiple_files_concatenated(self, tmp_path):
        file1 = tmp_path / "a.cl"
        file1.write_text("class A { };")
        file2 = tmp_path / "b.cl"
        file2.write_text("class Main { main(): Object { self }; };")
        output_file = tmp_path / "out.s"
        
        with patch.object(sys, "argv", ["pycoolc", str(file1), str(file2), "-o", str(output_file)]):
            result = main()
        
        assert result == 0
        content = output_file.read_text()
        # Check that class A was compiled (appears in class name table or init)
        assert "_class_name_A" in content or "_init_A" in content

    def test_compilation_error_returns_one(self, tmp_path):
        source_file = tmp_path / "bad.cl"
        source_file.write_text("class Main { x: UndefinedType; };")
        
        with patch.object(sys, "argv", ["pycoolc", str(source_file)]):
            result = main()
        
        assert result == 1

