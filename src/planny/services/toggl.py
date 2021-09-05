import requests
import json

class Toggl:
    def __init__(self, json_path):
        with open(json_path) as f:
            d = json.load(f)


