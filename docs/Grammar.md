# Grammar Specification

The following BNF grammar is based on the *COOL-2012* language specification (see: COOL Reference Manual).


```bnf
<program>                 ::= <classes>

<classes>                 ::= <classes> <class> ;
                          |   <class> ;

<class>                   ::= class TYPE <inheritance> { <features_list_opt> } ;

<inheritance>             ::= inherits TYPE
                          |   <empty>

<features_list_opt>       ::= <features_list>
                          |   <empty>

<features_list>           ::= <features_list> <feature> ;
                          |   <feature> ;

<feature>                 ::= ID ( <formal_params_list_opt> ) : TYPE { <expression> }
                          |   <formal>

<formal_params_list_opt>  ::= <formal_params_list>
                          |   <empty>

<formal_params_list>      ::= <formal_params_list> , <formal_param>
                          |   <formal_param>

<formal_param>            ::= ID : TYPE

<formal>                  ::= ID : TYPE <- <expression>
                          |   ID : TYPE

<expression>              ::= ID <- <expr>
                          |   <expression>.ID( <arguments_list_opt> )
                          |   <expression><at-type>.ID( <arguments_list_opt> )
                          |   <case>
                          |   <if_then_else>
                          |   <while>
                          |   <block_expression>
                          |   <let_expression>
                          |   new TYPE
                          |   isvoid <expr>
                          |   <expression> + <expression>
                          |   <expression> - <expression>
                          |   <expression> * <expression>
                          |   <expression> / <expression>
                          |   ~ <expression>
                          |   <expression> < <expression>
                          |   <expression> <= <expression>
                          |   <expression> = <expression>
                          |   not <expression>
                          |   ( <expression> )
                          |   SELF
                          |   ID
                          |   INTEGER
                          |   STRING
                          |   TRUE
                          |   FALSE

<arguments_list_opt>      ::= <arguments_list>
                          |   <empty>

<arguments_list>          ::= <arguments_list_opt> , <expression>
                          |   <expression>

<case>                    ::= case <expression> of <actions> esac

<action>                  ::= ID : TYPE => <expr>

<actions>                 ::= <action>
                          |   <action> <actions>

<if_then_else>            ::= if <expression> then <expression> else <expression> fi

<while>                   ::= while <expression> loop <expression> pool

<block_expression>        ::= { <block_list> }

<block_list>              ::= <block_list> <expression> ;
                          |   <expression> ;

<let_expression>          ::= let <formal> in <expression>
                          |   <nested_lets> , <formal>

 <nested_lets>            ::= <formal> IN <expression>
                          |   <nested_lets> , <formal>

<empty>                   ::=
```

