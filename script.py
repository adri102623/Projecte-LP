import streamlit as st
import pandas as pd
from antlr4 import *
from HinNerLexer import HinNerLexer
from HinNerParser import HinNerParser
from antlr4.error.ErrorListener import ErrorListener
from HinNerVisitor import HinNerVisitor
from graphviz import Digraph

class ASTTransformer(HinNerVisitor):
    def __init__(self):
        self.symbol_table = {}

    def visitVariable(self, ctx: HinNerParser.VariableContext):
        var_name = ctx.VAR().getText()
        return {'type': 'Var', 'name': var_name}

    def visitNumero(self, ctx: HinNerParser.NumeroContext):
        num_value = ctx.NUM().getText()
        return {'type': 'Num', 'value': num_value}

    def visitParens(self, ctx: HinNerParser.ParensContext):
        expr = self.visit(ctx.expr())
        return expr

    def visitOperacio(self, ctx: HinNerParser.OperacioContext):
        op_value = ctx.OP().getText()
        return {'type': 'Op', 'oper': op_value}

    def visitAbstraccion(self, ctx: HinNerParser.AbstraccionContext):
        var = ctx.VAR().getText()
        expr = self.visit(ctx.expr())
        return {
            'type': 'Abs',
            'var': {'type': 'Var', 'name': var},
            'expr': expr
        }

    def visitAplicacion(self, ctx: HinNerParser.AplicacionContext):
        func = self.visit(ctx.expr(0))
        arg = self.visit(ctx.expr(1))
        return {'type': 'App', 'func': func, 'arg': arg}

    def visitType(self, ctx: HinNerParser.TypeContext):
        expr = self.visit(ctx.expr())
        expr_str = self.expr_to_str(expr)
        type_ = self.visit(ctx.type_())
        type_str = self.type_to_str(type_)
        self.symbol_table[expr_str] = type_str
        return None  

    def visitTypeV(self, ctx: HinNerParser.TypeVContext):
        var_name = ctx.VAR().getText()
        return {'type': 'TypeV', 'name': var_name}

    def visitTypeArrow(self, ctx: HinNerParser.TypeArrowContext):
        from_var = ctx.VAR().getText()  
        to_type = self.visit(ctx.type_()) 
        return {'type': 'TypeArrow', 'from': {'type': 'TypeV', 'name': from_var}, 'to': to_type}

    def expr_to_str(self, expr):
        if expr['type'] == 'Var':
            return expr['name']
        elif expr['type'] == 'Num':
            return expr['value']
        elif expr['type'] == 'Op':
            return f"({expr['oper']})"
        elif expr['type'] == 'Abs':
            return f"\\{expr['var']['name']} -> {self.expr_to_str(expr['expr'])}"
        elif expr['type'] == 'Pre':
            return f"{expr['ope']['oper']} {self.expr_to_str(expr['expr'])}"
        elif expr['type'] == 'App':
            return f"{self.expr_to_str(expr['func'])} {self.expr_to_str(expr['arg'])}"
        else:
            return 'unknown_expr'
        
    def type_to_str(self, type_):
        if type_['type'] == 'TypeV':
            return type_['name']
        elif type_['type'] == 'TypeArrow':
            from_str = self.type_to_str(type_['from'])
            to_str = self.type_to_str(type_['to'])
            return f"({from_str} -> {to_str})" 
        else:
            return 'unknown_type'

    def defaultResult(self):
        return None


def next_letter(state):
    letter = state['current_letter']
    if letter == 'z':
        raise ValueError("Se han agotado las letras del abecedario")
    state['current_letter'] = chr(ord(letter) + 1)
    return letter


def show_semantic_tree_graph(sem_tree, taula_aux,state):
    dot = Digraph()

    def escape_html(s):
        return s.replace(">", "&gt;").replace("<", "&lt;") # Sino no em deixava posar els símbols < i > en els nodes

    def build_graph(tree, parent=None, taula_aux=None, state=None):
        if taula_aux is None:
            taula_aux = {}
        if state is None:
            state = {'current_letter': 'a'}

        if tree is None:
            st.error("Error: Nodo vacío encontrado en el árbol.")
            return

        current_node = str(id(tree))
        if parent:
            dot.edge(parent, current_node)

        node_label = ""
        node_type = tree.get('type', 'unknown')

        def extract_letters(type_str):
            letters = []
            for char in type_str:
                if char.isalpha():  
                    letters.append(char)
            return letters
    
        def get_or_assign_type(name):
            if name not in st.session_state.symbol_table and name not in taula_aux:
                taula_aux[name] = next_letter(state)
            if name in st.session_state.symbol_table:
                return st.session_state.symbol_table[name]
            return taula_aux[name]

        if node_type == 'Var':
            var_name = tree["name"]
            var_type = get_or_assign_type(var_name)
            node_label = f'{escape_html(var_name)}<br/>{escape_html(var_type)}'
        elif node_type == 'Num':
            num_value = tree["value"]
            num_type = get_or_assign_type(num_value)
            node_label = f'{escape_html(num_value)}<br/>{escape_html(num_type)}'
        elif node_type == 'Op':
            op_name = tree["oper"]
            op_type = get_or_assign_type(f"({op_name})")
            node_label = f'{"("+ op_name +")"}<br/>{escape_html(op_type)}'
        elif node_type == 'Abs':
            lambda_symbol = 'λ'
            node_label = f'{lambda_symbol}<br/>{next_letter(state)}'
            build_graph(tree['var'], current_node, taula_aux, state)
            build_graph(tree['expr'], current_node, taula_aux, state)
       
        elif node_type == 'App':
            arrob_symbol = '@'
            node_label = f'{arrob_symbol}<br/>{next_letter(state)}'
            build_graph(tree['func'], current_node, taula_aux, state)
            build_graph(tree['arg'], current_node, taula_aux, state)
        else:
            st.error(f"Unknown node type: {node_type}")
            node_label = 'unknown'

        if node_label:
            dot.node(current_node, f'<{node_label}>')

    build_graph(sem_tree, taula_aux=taula_aux,state=state)
    st.graphviz_chart(dot.source)


def show_type_tree_graph(sem_tree, taula_aux,state):
    dot = Digraph()

    def escape_html(s):
        return s.replace(">", "&gt;").replace("<", "&lt;") # Sino no em deixava posar els símbols < i > en els nodes

    def build_typegraph(tree, taula_aux, state, processed_vars, parent=None):
        if taula_aux is None:
            taula_aux = {}
        if state is None:
            state = {'current_letter': 'a'}
        if processed_vars is None:
            processed_vars = set()

        if tree is None:
            st.error("Error: Nodo vacío encontrado en el árbol.")
            return

        current_node = str(id(tree))
        if parent:
            dot.edge(parent, current_node)

        node_label = ""
        node_type = tree.get('type', 'unknown')

        def extract_letters(type_str):
            letters = []
            for char in type_str:
                if char.isalpha():  
                    letters.append(char)
            return letters

        def get_or_assign_type(name):
            if name not in st.session_state.symbol_table and name not in taula_aux:
                taula_aux[name] = next_letter(state)
            if name in st.session_state.symbol_table:
                return st.session_state.symbol_table[name]
            return taula_aux[name]

        if node_type == 'Var':
            var_name = tree["name"]
            if var_name not in st.session_state.symbol_table:
                next_letter(state)
            if var_name in processed_vars: # Si la variable ja ha sigut processada que no actualitzi la taula auxiliar
                if var_name in st.session_state.symbol_table:
                    var_type = st.session_state.symbol_table[var_name]
                    node_label = f'{escape_html(var_name)}<br/>{escape_html(var_type)}'
                else:
                    node_label = f'{escape_html(var_name)}<br/>{"N"}'
            else:
                var_type = get_or_assign_type(var_name)
                if var_name in st.session_state.symbol_table:
                    node_label = f'{escape_html(var_name)}<br/>{escape_html(var_type)}'
                elif var_name in taula_aux:
                    var = taula_aux[var_name]
                    taula_aux[var] = "N"
                    taula_aux.pop(var_name)
                    node_label = f'{escape_html(var_name)}<br/>{"N"}'
                processed_vars.add(var_name)

        elif node_type == 'Num':
            num_value = tree["value"]
            if num_value not in st.session_state.symbol_table:
                next_letter(state)
            if num_value in processed_vars:
                if num_value in st.session_state.symbol_table:
                    num_type = st.session_state.symbol_table[num_value]
                    node_label = f'{escape_html(num_value)}<br/>{escape_html(num_type)}'
                else:
                    node_label = f'{escape_html(num_value)}<br/>{"N"}'
            else:
                num_type = get_or_assign_type(num_value)
                if num_value in st.session_state.symbol_table:
                    node_label = f'{escape_html(num_value)}<br/>{escape_html(num_type)}'
                elif num_value in taula_aux:
                    num = taula_aux[num_value]
                    taula_aux.pop(num_value)
                    taula_aux[num] = "N"
                    node_label = f'{(num_value)}<br/>{"N"}'
                processed_vars.add(num_value)
               

        elif node_type == 'Op':
            op_name = tree["oper"]
            if op_name not in st.session_state.symbol_table:
                next_letter(state)
            op_type = get_or_assign_type(f"({op_name})")
            if f"({op_name})" in st.session_state.symbol_table:
                node_label = f'{"("+ op_name +")"}<br/>{escape_html(op_type)}'
            else:
                node_label =  f'{"("+ op_name +")"}<br/>(N {escape_html("->")} (N {escape_html("->")} N))'
                var = taula_aux[f"({op_name})"]
                taula_aux.pop(f"({op_name})")
                taula_aux[var] = f'(N -> (N -> N))'

        elif node_type == 'Abs':
            lambda_symbol = 'λ'
            letter = next_letter(state)
            if tree['var']['type'] == 'Var':
                var_name = tree['var']['name']
                if var_name in st.session_state.symbol_table:
                    var_type = st.session_state.symbol_table[var_name]
                    if var_type != "N":
                        st.error(f"Type Error: {var_type} vs N")
                    node_label = f'{lambda_symbol}<br/>( N {escape_html("->")} N)' # suposo que per els nostre casos sempre serà N
                    taula_aux[letter] = f'(N -> N)'
                else:
                    node_label = f'{lambda_symbol}<br/>({"N"} {escape_html("->")} {"N"})'
                    taula_aux[letter] = f'({"N"} -> {"N"})'
            build_typegraph(tree['var'], taula_aux, state, processed_vars, current_node)
            build_typegraph(tree['expr'], taula_aux, state, processed_vars, current_node)

        elif node_type == 'App':
            arrob_symbol = '@'
            letter = next_letter(state)

            if tree['func']['type'] == 'Op':
                type_func = get_or_assign_type(f"({tree['func']['oper']})")
                if tree['arg']['type'] == 'Num':
                    tipos = extract_letters(type_func)
                    lletra = tipos[0]
                if tree['arg']['type'] == 'Num':
                    type_arg = get_or_assign_type(f"{tree['arg']['value']}")
                    if f"({tree['func']['oper']})" in st.session_state.symbol_table:
                        if tree['arg']['value'] in st.session_state.symbol_table: # els dos valors estan guardats a la taula de tipus
                            if lletra != type_arg:
                                st.error(f"Type Error: {lletra} vs {type_arg}")
                            taula_aux[letter] = f'({(lletra)} -> {lletra})'
                        else: # nomes la operacio esta guardada a la taula de tipus
                            if lletra != "N":
                                st.error(f"Type Error: {lletra} vs N")
                            taula_aux[letter] = f'({(lletra)} -> {lletra})'
                        node_label = f'{arrob_symbol}<br/>({(lletra)} {escape_html("->")} {lletra})'
                    else:
                        if tree['arg']['value'] in st.session_state.symbol_table: # nomes el num esta guardat a la taula de tipus
                            node_label = f'{arrob_symbol}<br/>(N {escape_html("->")} {type_arg})'
                            if type_arg != "N":
                                st.error(f"Type Error: N vs {type_arg}")
                            taula_aux[letter] = f'(N -> N)'
                        else: # cap dels dos esta guardat a la taula de tipus (no pot haver error de tipus)
                            node_label = f'{arrob_symbol}<br/>(N {escape_html("->")} N)'
                            taula_aux[letter] = f'(N -> N)'
                else:
                    node_label = f'{arrob_symbol}<br/>{type_func}'
                    taula_aux[letter] = node_label
            else:
                node_label = f'{arrob_symbol}<br/>{"N"}'
                taula_aux[letter] = "N"

            build_typegraph(tree['func'], taula_aux, state, processed_vars, current_node)
            build_typegraph(tree['arg'], taula_aux, state, processed_vars, current_node)

        else:
            st.error(f"Unknown node type: {node_type}")
            node_label = 'unknown'

        if node_label:
            dot.node(current_node, f'<{node_label}>')

    build_typegraph(sem_tree, taula_aux, state, processed_vars=None)
    st.graphviz_chart(dot.source)
    

if 'symbol_table' not in st.session_state:
    st.session_state.symbol_table = {}

def main():
    st.title("Comprobador de Expresiones Haskell")
    expression = st.text_input("Introduce una expresión/definicion de tipos:")
    if st.button("Comprueba"):
        lexer = HinNerLexer(InputStream(expression))
        stream = CommonTokenStream(lexer)
        parser = HinNerParser(stream)
        tree = parser.root()
        if parser.getNumberOfSyntaxErrors() == 0:
            st.success("La expresión es válida")
            transformer = ASTTransformer()
            sem_tree = transformer.visit(tree)
            taula_aux = {}
            state = {'current_letter': 'a'}
            if sem_tree:
                show_semantic_tree_graph(sem_tree, taula_aux,state)
            st.session_state.symbol_table.update(transformer.symbol_table)

            st.subheader("Tabla de Tipos:")
            symbol_table_df = pd.DataFrame(
                list(st.session_state.symbol_table.items()), columns=['Nombre del Símbolo', 'Tipo']
            )
            st.table(symbol_table_df.set_index('Nombre del Símbolo'))
            state = {'current_letter': 'a'}
            
        
            if sem_tree:
                show_type_tree_graph(sem_tree, taula_aux,state)
                taula_aux_df = pd.DataFrame(
                list(taula_aux.items()), columns=['Variable', 'Tipo']
                  )
                st.table(taula_aux_df.set_index('Variable'))
            
        else:
            st.error("La expresión no es válida")
if __name__ == "__main__":
    main()
