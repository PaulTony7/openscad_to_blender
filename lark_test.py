from lark import Lark
json_parser = Lark(r"""
    ?value: dictp
        | list
        | string
        | SIGNED_NUMBER -> number
        | "true"        -> true
        | "false"       -> false
        | "null"        -> null
    list : "[" [value ("," value)*] "]"

    dict : "{" [pair ("," pair)*] "}"
    pair : ESCAPED_STRING ":" value

    string : ESCAPED_STRING

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
    """, start='value')

text = '{"key": ["item0", "item1", 3.14]}'

print(json_parser.parse(text).pretty())