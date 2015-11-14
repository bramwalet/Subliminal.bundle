# coding=utf-8

# restore builtins


def restore_builtins(module, base):
    setattr(module, "__builtins__", getattr(getattr(
        [x for x in getattr(getattr(getattr(base, "__class__"), "__base__"), "__subclasses__")() if getattr(x, "__name__") == 'catch_warnings'][
            0](),
        "_module"),
        "__builtins__"))
