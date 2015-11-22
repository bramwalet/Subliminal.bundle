# coding=utf-8

# restore builtins


def restore_builtins(module, base):
    module.__builtins__ = [x for x in base.__class__.__base__.__subclasses__() if x.__name__ == 'catch_warnings'][0]()._module.__builtins__
