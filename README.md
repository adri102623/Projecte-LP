# Projecte LP

En aquest projecte podras trobar un petit analitzador de tipus anomenat HinNer que pot codificar nombres naturals, variables, alguns operadors en notació prefixa, parèntesis, l'aplicació i l'abstracció en llenguatge tipus Haskell amb un sistema d'inferència de tipus seguint el algorisme de Hindley-Milner.

## Instalació

### Instalar Antlr
```bash
pip install antlr4-tools antlr4
pip install antlr4-python3-runtime
```
### Instalar Streamlit
```bash
pip install streamlit
```
## Execució

### Executar ANTLR
```bash
antlr4 -Dlanguage=Python3 -no-listener -visitor HinNer.g4  
```
### Exectuar Streamlit
```bash
streamlit run script.py
```

## Usage

### Introduir una expresió
```bash
Introduce una expresion:
\x -> (+) 2 x
```
### Introduir una definició de tipus
```bash
Introduce una expresion:
(+) :: N -> N -> N
```



