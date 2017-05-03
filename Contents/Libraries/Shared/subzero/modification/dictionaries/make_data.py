# coding=utf-8

import os
import pprint
from collections import OrderedDict

from bs4 import BeautifulSoup

TEMPLATE = """\
from collections import OrderedDict
data = """


if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    xml_dir = os.path.join(cur_dir, "xml")
    file_list = os.listdir(xml_dir)

    data = {}

    for fn in file_list:
        if fn.endswith("_OCRFixReplaceList.xml"):
            lang = fn.split("_")[0]
            soup = BeautifulSoup(open(os.path.join(xml_dir, fn)), "xml")

            data[lang] = {"full": OrderedDict(), "partial": OrderedDict()}

            for wanted in ("WholeLines", "WholeWords", "PartialWordsAlways"):
                for grp in soup.find_all(wanted):
                    for line in grp.find_all(["Line", "Word", "WordPart"]):
                        data[lang]["full"][line["from"]] = line["to"]

                    for line in grp.find_all(["WordPart"]):
                        data[lang]["partial"][line["from"]] = line["to"]

    f = open(os.path.join(cur_dir, "data.py"), "w+")
    f.write(TEMPLATE)
    f.write(pprint.pformat(data, width=1))
    f.close()
