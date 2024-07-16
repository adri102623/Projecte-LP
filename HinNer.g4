grammar HinNer;

root
     : (expr|typeDeclaration)
     ;

expr : '(' expr ')'          # Parens
    | expr expr              # Aplicacion
    | '\\' VAR '->' expr     # Abstraccion
    | '(' OP ')'             # Operacio
    | NUM                    # Numero
    | VAR                    # Variable
    ;

typeDeclaration
    : expr '::' type_        #Type
    ;

type_ : VAR                  # TypeV
    | VAR '->' type_       # TypeArrow
    ;


VAR : [a-zA-Z]+ ;
NUM : [0-9]+ ;
OP  : '+' | '-' | '*' | '/' ;
WS  : [ \t\r\n]+ -> skip ;
