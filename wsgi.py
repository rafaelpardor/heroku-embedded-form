import os, logging

from dotenv import load_dotenv

from main import app

load_dotenv(".env")

if __name__ == "__main__":
    app.debug = os.environ['test_mode']
    PORT = os.environ['port'] if os.environ['port'] == None else 5000
    app.run(port=PORT)
    logging.basicConfig(filename='lyra.log', level=logging.DEBUG)