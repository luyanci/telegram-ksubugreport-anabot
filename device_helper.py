import csv
import logging

logger = logging.getLogger(__name__)

def _source_priority(source_file: str) -> int:
    if source_file.endswith("_en"):
        return 2
    if source_file.endswith("_cn"):
        return 0
    return 1


def _device_key(model: str, brand: str, code_alias: str, model_name: str) -> tuple:
    aliases = tuple(sorted(alias.strip().casefold() for alias in code_alias.split(",") if alias.strip()))
    identity = aliases or (model_name.strip().casefold(),)
    return brand.strip().casefold(), model.strip().casefold(), identity


def _load_model_data() -> list[list[str]]:
    model_data_by_key = {}
    source_priority_by_key = {}
    with open("./models.csv", encoding="utf-8-sig", newline="") as file_datas:
        for data in csv.DictReader(file_datas):
            model = data["model"]
            brand = data["brand"]
            code_alias = data["code_alias"]
            model_name = data["model_name"]
            version_name = data["ver_name"]
            source_file = data["source_file"]
            key = _device_key(model, brand, code_alias, model_name)
            priority = _source_priority(source_file)
            if key not in model_data_by_key or priority > source_priority_by_key[key]:
                model_data_by_key[key] = [model, brand, code_alias, model_name, version_name]
                source_priority_by_key[key] = priority
    return list(model_data_by_key.values())


model_datas = _load_model_data()