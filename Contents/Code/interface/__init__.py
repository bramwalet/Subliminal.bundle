import sys

import menu
sys.modules["interface.menu"] = menu

import menu_helpers
sys.modules["interface.menu_helpers"] = menu_helpers