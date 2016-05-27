## COOL's Context-Free Grammar

The following is a formalization of COOL's Context-Free Grammar in Backus-Naur Form (BNF). The grammar specifies COOL as per the 2012 specification, which is part of the COOL Reference Manual.

A preliminary note on the meaning of postfixes in left-hand-side symbols:

  * `ne` is an abbreviation for "Not Empty", which means that the given production rule doesn't directly produce the empty string.
  * `woa` is an abbreviation for "Without Assignment", which means that the given production rule doesn't produce `formal` Symbols with assignment.

### Grammar

```bnf
<program>        ::= <classes>

<classes>        ::= <class>
                 |   <class> <classes>

<class>          ::= class TYPE <inheritance> { <features> } ;

<inheritance>    ::= inherits TYPE
                 |   ""

<features>       ::= <feature> <features>
                 |   ""

<feature>        ::= ID ( <formals-woa> ) : TYPE { <expr> } ;
                 |   <formal> ;

<formals>        ::= <formal>
                 |   <formal>, <formals-ne>
                 |   ""
                
<formals-ne>     ::= <formal>
                 |   <formal>, <formals-ne>

<formal>         ::= ID : TYPE
                 |   ID : TYPE <- <expr>

<formals-woa>    ::= <formal-woa>
                 |   <formal-woa>, <formals-woa-ne>
                 |   ""

<formals-woa-ne> ::= <formal-woa>
                 |   <formal-woa>, <formals-woa-ne>

<formal-woa>     ::= ID : TYPE

<exprns>         ::= <expr>
                 |   <expr>, <exprns-ne>
                 |   ""

<exprns-ne>      ::= <expr>
                 |   <expr>, <exprns-ne>

<expr>           ::= ID <- <expr>
                 |   <expr><at-type>.ID( <exprns> )
                 |   <if-then-else>
                 |   <while>
                 |   { <exprns-ne> }
                 |   <let>
                 |   <case>
                 |   new TYPE
                 |   isvoid <expr>
                 |   <expr> + <expr>
                 |   <expr> - <expr>
                 |   <expr> * <expr>
                 |   <expr> / <expr>
                 |   ~ <expr>
                 |   <expr> < <expr>
                 |   <expr> <= <expr>
                 |   <expr> = <expr>
                 |   not <expr>
                 |   (<expr>)
                 |   ID
                 |   integer
                 |   string
                 |   true
                 |   false

<at-type>        ::= @TYPE
                 |   ""

<actions>        ::= <action>
                 |   <action> <actions>

<action>         ::= ID : TYPE => <expr>

<if-then-else>   ::= if <expr> then <expr> else <expr> fi

<while>          ::= while <expr> loop <expr> pool

<let>            ::= let <formals-ne> in <expr>

<case>           ::= case <expr> of <actions> esac
```

