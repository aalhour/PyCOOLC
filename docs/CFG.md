## COOL's Context-Free Grammar

The following is a formalization of COOL's Context-Free Grammar in Backus-Naur Form (BNF).

```bnf
<program>   ::= [<class>;]+

<class>     ::= class TYPE [ inherits TYPE ] { [<feature>;]* }

<feature>   ::= ID( [ <formal> [, <formal>]* ] ) : TYPE { <expr> }
            |   ID : TYPE [ <- <expr> ]

<formal>    ::= ID : TYPE

<expr>      ::= ID <- <expr>
            |   <expr>[@TYPE].ID( [ <expr> [, <expr>]* ] )
            |   if <expr> then <expr> else <expr> fi
            |   while <expr> loop <expr> pool
            |   { [<expr>;]+ }
            |   let ID : TYPE [ <- <expr> ] [, ID : TYPE [ <- <expr> ] ]* in <expr>
            |   case <expr> of [ ID : TYPE => <expr>; ]+ esac
            |   new TYPE
            |   isvoid <expr>
            |   <expr> + <expr>
            |   <expr> - <expr>
            |   <expr> * <expr>
            |   <expr> / <expr>
            |   ~<expr>
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
```

The previous Formal Language specification was translated from the COOL Reference Manual \[2012\], by Alex Aiken.