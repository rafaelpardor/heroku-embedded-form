import hashlib, base64, hmac, json

from flask import Flask, request
import yaml

app = Flask(__name__)

def read_yaml(file):
    with open(file) as f:
        return json.loads(json.dumps(yaml.load(f, Loader=yaml.FullLoader)))


def encode_to_base64(str_to_encode):
    return base64.b64encode(str_to_encode.encode('ascii')).decode()


def compute_hmac_sha256_signature(key, message):
    """
    `key` argument is the password of the store
    `message` argument is all the arguments concatenated, plus the password store
    """
    byte_key = str.encode(key)
    message = str.encode(message)
    signature = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
    return signature


def url_parser(obj_dict) -> str:
    """
    Create URL for the form
    """
    url_str = ''
    for i in obj_dict.keys():
        if i != "currency":
            url_str += f"{i}={obj_dict[i] if obj_dict[i] != '' else 'null'}&" if type(obj_dict[i]) != dict else ''
        if type(obj_dict[i]) == dict:
            url_str += url_parser(obj_dict[i])
    return url_str


def assign_parameters(obj_dict):
    for value in obj_dict.keys():
        if request.args.get(value) != None:
            obj_dict[value] = request.args.get(value)
        if type(obj_dict[value]) == dict:
            assign_parameters(obj_dict[value])
    return obj_dict


def new_body_to_send(obj_dict):
    """
    Create a new object with the incoming data from the form
    """
    new_body = {}
    for value in obj_dict.keys():
        try:
            if request.form[value] != "null":
                new_body[value] = request.form[value]
        except KeyError:
            app.logger.error(f'"{value}" not found or is a key.')
            pass
        if type(obj_dict[value]) == dict:
            new_body[value] = new_body_to_send(obj_dict[value])
    app.logger.info("Body to send:", new_body)

    return new_body
