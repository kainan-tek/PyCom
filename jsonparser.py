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
        self.file: str = _file

    def file_read(self, encode: str = "utf-8") -> tuple[JsonFlag, dict]:
        """
        Read json file and return the json dict.

        Args:
            encode (str): encoding of the file

        Returns:
            tuple[JsonFlag, dict]: result flag and the json dict
        """
        json_dict: dict = {}

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

    def file_write(self, _json_dict: dict = {}, encode: str = "utf-8") -> JsonFlag:
        """
        Write a json dict into a file.

        Args:
            _json_dict (dict, optional): The json dict to be written. Defaults to {}.
            encode (str, optional): The encoding of the file. Defaults to "utf-8".

        Returns:
            JsonFlag: The result of writing the json dict.
        """
        if not os.path.exists(self.file):
            return JsonFlag.NO_FILE  # file not exists, return no file flag

        try:
            with open(self.file, mode='w+', encoding=encode) as fp:
                json.dump(_json_dict, fp, indent=4, ensure_ascii=False)
        except Exception:
            return JsonFlag.ERR_OPEN_W  # error occurs, return error open write flag

        return JsonFlag.SUCCESS  # write successfully, return success flag
