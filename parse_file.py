
import os
import json
from enum import Enum


class JsonFlag(Enum):
    SUCCESS = 0
    NO_FILE = 1
    ERR_OPEN_R = 2
    ERR_OPEN_W = 3
    EMPTY_DICT = 4


class JsonParse():
    def __init__(self, _file):
        self.file = _file

    def file_read(self):
        json_dict = {}

        if not os.path.exists(self.file):
            return (JsonFlag.NO_FILE, json_dict)

        try:
            with open(self.file, mode='r', encoding="utf-8") as fp:
                json_dict = json.load(fp)
        except Exception:
            return (JsonFlag.ERR_OPEN_R, json_dict)

        if not json_dict:
            return (JsonFlag.EMPTY_DICT, json_dict)

        return (JsonFlag.SUCCESS, json_dict)

    def file_write(self, _json_dict={}):
        if not os.path.exists(self.file):
            return JsonFlag.NO_FILE

        try:
            with open(self.file, mode='w+', encoding="utf-8") as fp:
                json.dump(_json_dict, fp, indent=4, ensure_ascii=False)
        except Exception:
            return JsonFlag.ERR_OPEN_W

        return JsonFlag.SUCCESS
