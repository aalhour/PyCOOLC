#!/usr/bin/env python3

"""
AST to TAC (Three-Address Code) Translator for COOL.

# Translation Overview

This module translates COOL's Abstract Syntax Tree into Three-Address Code,
which is a lower-level intermediate representation suitable for optimization
and analysis.

The translation follows these principles:

1. **Flatten expressions**: Complex nested expressions become sequences
   of simple three-address instructions.
   
2. **Explicit control flow**: if/while/case become labels and jumps.

3. **Temporaries for intermediate values**: Each subexpression result
   gets a temporary variable.

4. **Linearize**: Tree structure becomes a list of instructions.

# Translation Rules

For each AST node type, we define a translation rule:

    [[Integer(n)]] = t = n

    [[a + b]]      = t1 = [[a]]
                     t2 = [[b]]
                     t3 = t1 + t2

    [[if p then t else e fi]] = 
                     tc = [[p]]
                     ifnot tc goto else_label
                     tt = [[t]]
                     t = tt
                     goto end_label
                     else_label:
                     te = [[e]]
                     t = te
                     end_label:

"""

from __future__ import annotations

from dataclasses import dataclass, field

from pycoolc import ast as AST
from pycoolc.ir.tac import (
    Instruction, Operand, Temp, Var, Const, Label,
    BinOp, UnaryOp,
    BinaryOp, UnaryOperation, Copy,
    LabelInstr, Jump, CondJump, CondJumpNot,
    Param, Call, Return,
    New, Dispatch, StaticDispatch, IsVoid, GetAttr, SetAttr,
    Phi, Comment,
    TACMethod, TACProgram, TempGenerator, LabelGenerator,
)


@dataclass
class TranslatorContext:
    """
    Context for translation, tracking:
    - Current class name (for self type resolution)
    - Current method name
    - Variable bindings (name -> Var/Temp)
    - Attribute list (for attribute access)
    """
    class_name: str
    method_name: str
    temp_gen: TempGenerator
    label_gen: LabelGenerator
    
    # Scope stack: each scope maps variable names to operands
    scopes: list[dict[str, Operand]] = field(default_factory=list)
    
    # Class attributes for the current class
    attributes: dict[str, str] = field(default_factory=dict)  # name -> type
    
    def push_scope(self) -> None:
        """Enter a new scope (for let/case)."""
        self.scopes.append({})
    
    def pop_scope(self) -> None:
        """Exit the current scope."""
        self.scopes.pop()
    
    def define(self, name: str, operand: Operand) -> None:
        """Define a variable in the current scope."""
        if self.scopes:
            self.scopes[-1][name] = operand
    
    def lookup(self, name: str) -> Operand | None:
        """Look up a variable, searching from innermost to outermost scope."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def new_temp(self) -> Temp:
        """Generate a fresh temporary."""
        return self.temp_gen.next()
    
    def new_label(self, hint: str = "") -> Label:
        """Generate a fresh label."""
        return self.label_gen.next(hint)


class ASTToTACTranslator:
    """
    Translates COOL AST to Three-Address Code.
    
    Usage:
        translator = ASTToTACTranslator()
        tac_program = translator.translate(ast_program)
    """
    
    def __init__(self) -> None:
        self.temp_gen = TempGenerator()
        self.label_gen = LabelGenerator()
        
        # Class information (populated during translation)
        self.class_attributes: dict[str, dict[str, str]] = {}  # class -> {attr -> type}
    
    def translate(self, program: AST.Program) -> TACProgram:
        """Translate an entire COOL program to TAC."""
        methods: list[TACMethod] = []
        
        # First pass: collect class attributes
        for cls in program.classes:
            self._collect_attributes(cls)
        
        # Second pass: translate methods
        for cls in program.classes:
            for feature in cls.features:
                if isinstance(feature, AST.ClassMethod):
                    tac_method = self._translate_method(cls, feature)
                    methods.append(tac_method)
        
        return TACProgram(methods=methods)
    
    def _collect_attributes(self, cls: AST.Class) -> None:
        """Collect attribute information for a class."""
        attrs: dict[str, str] = {}
        for feature in cls.features:
            if isinstance(feature, AST.ClassAttribute):
                attrs[feature.name] = feature.attr_type
        self.class_attributes[cls.name] = attrs
    
    def _translate_method(self, cls: AST.Class, method: AST.ClassMethod) -> TACMethod:
        """Translate a single method to TAC."""
        self.temp_gen.reset()
        
        ctx = TranslatorContext(
            class_name=cls.name,
            method_name=method.name,
            temp_gen=self.temp_gen,
            label_gen=self.label_gen,
            attributes=self.class_attributes.get(cls.name, {}),
        )
        
        # Create initial scope with 'self' and parameters
        ctx.push_scope()
        ctx.define("self", Var("self"))
        
        for param in method.formal_params:
            ctx.define(param.name, Var(param.name))
        
        # Translate method body
        instructions: list[Instruction] = []
        instructions.append(Comment(f"Method {cls.name}.{method.name}"))
        
        result = self._translate_expr(method.body, ctx, instructions)
        
        # Add return
        instructions.append(Return(result))
        
        ctx.pop_scope()
        
        return TACMethod(
            class_name=cls.name,
            method_name=method.name,
            params=[p.name for p in method.formal_params],
            instructions=instructions,
        )
    
    def _translate_expr(
        self,
        expr: AST.AST,
        ctx: TranslatorContext,
        instrs: list[Instruction],
    ) -> Operand:
        """
        Translate an expression to TAC.
        
        Returns the operand holding the expression's result.
        Appends instructions to the instrs list.
        """
        match expr:
            # --- Constants ---
            case AST.Integer(content=value):
                t = ctx.new_temp()
                instrs.append(Copy(t, Const(value, "Int")))
                return t
            
            case AST.String(content=value):
                t = ctx.new_temp()
                instrs.append(Copy(t, Const(value, "String")))
                return t
            
            case AST.Boolean(content=value):
                t = ctx.new_temp()
                instrs.append(Copy(t, Const(value, "Bool")))
                return t
            
            # --- Variables ---
            case AST.Self():
                return Var("self")
            
            case AST.Object(name=name):
                # Check local scope first
                local = ctx.lookup(name)
                if local is not None:
                    return local
                
                # Must be an attribute
                if name in ctx.attributes:
                    t = ctx.new_temp()
                    instrs.append(GetAttr(t, Var("self"), name))
                    return t
                
                # Undefined variable (should be caught by semantic analysis)
                return Var(name)
            
            # --- Assignment ---
            case AST.Assignment(instance=name, expr=rhs):
                rhs_val = self._translate_expr(rhs, ctx, instrs)
                
                # Check if it's a local variable
                local = ctx.lookup(name)
                if local is not None:
                    if isinstance(local, Var):
                        instrs.append(Copy(local, rhs_val))
                    else:
                        # Reassigning a temp - create new binding
                        ctx.define(name, rhs_val)
                    return rhs_val
                
                # Must be an attribute
                instrs.append(SetAttr(Var("self"), name, rhs_val))
                return rhs_val
            
            # --- Arithmetic ---
            case AST.Addition(first=left, second=right):
                return self._translate_binop(BinOp.ADD, left, right, ctx, instrs)
            
            case AST.Subtraction(first=left, second=right):
                return self._translate_binop(BinOp.SUB, left, right, ctx, instrs)
            
            case AST.Multiplication(first=left, second=right):
                return self._translate_binop(BinOp.MUL, left, right, ctx, instrs)
            
            case AST.Division(first=left, second=right):
                return self._translate_binop(BinOp.DIV, left, right, ctx, instrs)
            
            # --- Comparisons ---
            case AST.LessThan(first=left, second=right):
                return self._translate_binop(BinOp.LT, left, right, ctx, instrs)
            
            case AST.LessThanOrEqual(first=left, second=right):
                return self._translate_binop(BinOp.LE, left, right, ctx, instrs)
            
            case AST.Equal(first=left, second=right):
                return self._translate_binop(BinOp.EQ, left, right, ctx, instrs)
            
            # --- Unary operations ---
            case AST.IntegerComplement(integer_expr=operand):
                op_val = self._translate_expr(operand, ctx, instrs)
                t = ctx.new_temp()
                instrs.append(UnaryOperation(t, UnaryOp.NEG, op_val))
                return t
            
            case AST.BooleanComplement(boolean_expr=operand):
                op_val = self._translate_expr(operand, ctx, instrs)
                t = ctx.new_temp()
                instrs.append(UnaryOperation(t, UnaryOp.NOT, op_val))
                return t
            
            # --- Block ---
            case AST.Block(expr_list=exprs):
                result: Operand = Const(0, "Int")  # Default
                for e in exprs:
                    result = self._translate_expr(e, ctx, instrs)
                return result
            
            # --- If-then-else ---
            case AST.If(predicate=pred, then_body=then_expr, else_body=else_expr):
                else_label = ctx.new_label("else")
                end_label = ctx.new_label("endif")
                result = ctx.new_temp()
                
                # Evaluate predicate
                pred_val = self._translate_expr(pred, ctx, instrs)
                instrs.append(CondJumpNot(pred_val, else_label))
                
                # Then branch
                then_val = self._translate_expr(then_expr, ctx, instrs)
                instrs.append(Copy(result, then_val))
                instrs.append(Jump(end_label))
                
                # Else branch
                instrs.append(LabelInstr(else_label))
                else_val = self._translate_expr(else_expr, ctx, instrs)
                instrs.append(Copy(result, else_val))
                
                instrs.append(LabelInstr(end_label))
                return result
            
            # --- While loop ---
            case AST.WhileLoop(predicate=pred, body=body):
                loop_label = ctx.new_label("while")
                end_label = ctx.new_label("endwhile")
                
                instrs.append(LabelInstr(loop_label))
                
                # Evaluate predicate
                pred_val = self._translate_expr(pred, ctx, instrs)
                instrs.append(CondJumpNot(pred_val, end_label))
                
                # Loop body
                self._translate_expr(body, ctx, instrs)
                instrs.append(Jump(loop_label))
                
                instrs.append(LabelInstr(end_label))
                
                # While returns void (Object in COOL)
                t = ctx.new_temp()
                instrs.append(Copy(t, Var("self")))  # Return self as placeholder
                return t
            
            # --- Let ---
            case AST.Let(instance=name, return_type=var_type, init_expr=init, body=body):
                ctx.push_scope()
                
                # Initialize variable
                var = ctx.new_temp()
                if init is not None:
                    init_val = self._translate_expr(init, ctx, instrs)
                    instrs.append(Copy(var, init_val))
                else:
                    # Default initialization
                    instrs.append(Copy(var, self._default_value(var_type)))
                
                ctx.define(name, var)
                
                # Translate body
                result = self._translate_expr(body, ctx, instrs)
                
                ctx.pop_scope()
                return result
            
            # --- Case ---
            case AST.Case(expr=case_expr, actions=branches):
                case_val = self._translate_expr(case_expr, ctx, instrs)
                result = ctx.new_temp()
                end_label = ctx.new_label("endcase")
                
                # Generate branch checks and bodies
                for i, action in enumerate(branches):
                    next_label = ctx.new_label(f"case_{i + 1}") if i < len(branches) - 1 else end_label
                    
                    # Type check (simplified - real implementation needs runtime type check)
                    # For now, generate code for each branch sequentially
                    ctx.push_scope()
                    
                    # Bind the variable
                    var = ctx.new_temp()
                    instrs.append(Copy(var, case_val))
                    ctx.define(action.name, var)
                    
                    # Branch body
                    branch_val = self._translate_expr(action.body, ctx, instrs)
                    instrs.append(Copy(result, branch_val))
                    instrs.append(Jump(end_label))
                    
                    ctx.pop_scope()
                    
                    if i < len(branches) - 1:
                        instrs.append(LabelInstr(next_label))
                
                instrs.append(LabelInstr(end_label))
                return result
            
            # --- New ---
            case AST.NewObject(type=type_name):
                t = ctx.new_temp()
                instrs.append(New(t, type_name))
                return t
            
            # --- IsVoid ---
            case AST.IsVoid(expr=operand):
                op_val = self._translate_expr(operand, ctx, instrs)
                t = ctx.new_temp()
                instrs.append(IsVoid(t, op_val))
                return t
            
            # --- Dynamic dispatch ---
            case AST.DynamicDispatch(instance=obj, method=method_name, arguments=args):
                obj_val = self._translate_expr(obj, ctx, instrs)
                
                # Evaluate and push arguments
                for arg in args:
                    arg_val = self._translate_expr(arg, ctx, instrs)
                    instrs.append(Param(arg_val))
                
                t = ctx.new_temp()
                instrs.append(Dispatch(t, obj_val, method_name, len(args)))
                return t
            
            # --- Static dispatch ---
            case AST.StaticDispatch(instance=obj, dispatch_type=static_type, 
                                    method=method_name, arguments=args):
                obj_val = self._translate_expr(obj, ctx, instrs)
                
                # Evaluate and push arguments
                for arg in args:
                    arg_val = self._translate_expr(arg, ctx, instrs)
                    instrs.append(Param(arg_val))
                
                t = ctx.new_temp()
                instrs.append(StaticDispatch(t, obj_val, static_type, method_name, len(args)))
                return t
            
            case _:
                # Fallback for unhandled expressions
                instrs.append(Comment(f"Unhandled: {type(expr).__name__}"))
                t = ctx.new_temp()
                instrs.append(Copy(t, Const(0, "Int")))
                return t
    
    def _translate_binop(
        self,
        op: BinOp,
        left: AST.AST,
        right: AST.AST,
        ctx: TranslatorContext,
        instrs: list[Instruction],
    ) -> Operand:
        """Translate a binary operation."""
        left_val = self._translate_expr(left, ctx, instrs)
        right_val = self._translate_expr(right, ctx, instrs)
        t = ctx.new_temp()
        instrs.append(BinaryOp(t, op, left_val, right_val))
        return t
    
    def _default_value(self, type_name: str) -> Operand:
        """Return the default value for a type."""
        match type_name:
            case "Int":
                return Const(0, "Int")
            case "Bool":
                return Const(False, "Bool")
            case "String":
                return Const("", "String")
            case _:
                # Object types default to void (represented as 0/null)
                return Const(0, "Int")  # Placeholder for void


def translate_to_tac(program: AST.Program) -> TACProgram:
    """Convenience function to translate AST to TAC."""
    translator = ASTToTACTranslator()
    return translator.translate(program)

