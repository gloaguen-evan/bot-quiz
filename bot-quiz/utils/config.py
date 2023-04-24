import yaml
import json
import csv

from pathlib import Path

path_file = Path(__file__)
path_main = path_file.parent.parent
path_config = path_main / 'configs'


def load_auth_config():
    path_auth_config = path_config / "auth_config.yaml"
    with open(path_auth_config, 'r') as f:
        return yaml.safe_load(f)


def load_quiz_config() -> dict:
    path_quiz_config = path_config / 'quiz_config.json'
    with open(path_quiz_config, 'r') as f:
        return json.load(f)


def load_csv_question() -> list[dict]:
    path_question = path_config / 'qcm.csv'
    data = []
    with open(path_question, 'r', encoding="utf-8") as csv_file:
        my_reader = csv.DictReader(csv_file, delimiter=';', quotechar='"')
        for row in my_reader:
            dict_row = dict(row)
            if _ := [v for v in dict_row.values() if v is None]:
                continue
            data.append(dict_row)
        return data
