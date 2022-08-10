from glob import glob
import json

import numpy as np
import yaml


class NumpyEncoder(json.JSONEncoder):
    """
    Special json encoder for numpy types. Numpy types are not accepted by the
    json encoder and need to be converted to python types.
    """

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)



class YamlWorker:
    @staticmethod
    def load_yaml(path=None):
        if path is None:
            file_name = glob("*.yaml")[0]
        else:
            file_name = glob(f"{path}/*.yaml")[0]
        with open(file_name, "r") as file:
            yaml_file = yaml.safe_load(file)
        return yaml_file

    @staticmethod
    def save_yaml(dictionary, save_filename):
        with open(f"{save_filename}.yaml", "w") as file:
            yaml.dump(dictionary, file)

