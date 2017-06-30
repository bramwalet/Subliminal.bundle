import sys

import menu
sys.modules["interface.menu"] = menu
sys.modules["menu"] = menu

import menu_helpers
sys.modules["interface.menu_helpers"] = menu_helpers

import advanced
sys.modules["interface.advanced"] = advanced

import main
sys.modules["interface.main"] = main

import refresh_item
sys.modules["interface.refresh_item"] = refresh_item

import item_details
sys.modules["interface.item_details"] = item_details

import sub_mod
sys.modules["interface.modification"] = sub_mod
