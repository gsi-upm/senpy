import os

strict = os.environ.get('SENPY_STRICT', '').lower() not in ["", "false", "f"]
data_folder = os.environ.get('SENPY_DATA', None)
if data_folder:
    data_folder = os.path.abspath(data_folder)
testing = os.environ.get('SENPY_TESTING', "") != ""
