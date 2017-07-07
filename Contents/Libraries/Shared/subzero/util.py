# coding=utf-8
import os


def get_root_path():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))