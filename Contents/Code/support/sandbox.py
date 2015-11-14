# coding=utf-8


# dummy test to see if we can restore globals() and builtins
# not used :)

import pprint
import sys

thismodule = sys.modules[__name__]
setattr(thismodule, "__builtins__", getattr(getattr(
    [x for x in getattr(getattr(getattr({}, "__class__"), "__base__"), "__subclasses__")() if getattr(x, "__name__") == 'catch_warnings'][0](),
    "_module"),
    "__builtins__"))

globals = getattr(thismodule, "__builtins__")["globals"]

for key, value in getattr(thismodule, "__builtins__").iteritems():
    if key != "globals":
        getattr(thismodule, "globals")()[key] = value

pprint.pprint(globals())
print iter
