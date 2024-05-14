import json
import os
from enum import Enum


class JsonFlag(Enum):
    SUCCESS = 0
    NO_FILE = 1
    ERR_OPEN_R = 2
    ERR_OPEN_W = 3
    EMPTY_DICT = 4


class JsonParser():
    def __init__(self, _file):
        self.file = _file

    def file_read(self, encode="utf-8") -> tuple[JsonFlag, dict]:
        """
        Read json dict from file.

        Parameters:
            encode (str): encoding of the file, default is "utf-8"

        Returns:
            (JsonFlag, dict): result flag and json dict
        """
        json_dict = {}

        if not os.path.exists(self.file):
            return JsonFlag.NO_FILE, json_dict  # file not exists, return no file flag

        try:
            with open(self.file, mode='r', encoding=encode, newline='') as fp:
                json_dict = json.load(fp)
        except Exception:
            return JsonFlag.ERR_OPEN_R, json_dict  # error occurs, return error open read flag

        if not json_dict:
            return (JsonFlag.EMPTY_DICT, json_dict)  # json dict is empty, return empty dict flag

        return JsonFlag.SUCCESS, json_dict  # read json successfully, return success flag

    def file_write(self, _json_dict={}, encode="utf-8") -> JsonFlag:
        """
        Write json dict to file.
        Parameters:
            _json_dict: dict, json dict to write
            encode: str, encoding of the file
        Returns:
            JsonFlag, result flag
        """
        if not os.path.exists(self.file):
            return JsonFlag.NO_FILE  # file not exists, return no file flag

        try:
            with open(self.file, mode='w+', encoding=encode) as fp:
                json.dump(_json_dict, fp, indent=4, ensure_ascii=False)
        except Exception:
            return JsonFlag.ERR_OPEN_W  # error occurs, return error open write flag

        return JsonFlag.SUCCESS  # write successfully, return success flag
