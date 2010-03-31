import sys

def get_func_argcount(func):
    if sys.hexversion > 0x03000000:
        return func.__code__.co_argcount
    else:
        return func.func_code.co_argcount
        
def input_prompt(prompt):
    if sys.hexversion > 0x03000000:
        return input(prompt)
    else:
        return raw_input(prompt)