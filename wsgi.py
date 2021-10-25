import os, logging

from dotenv import load_dotenv

from main import app

load_dotenv(".env")

TEST_MODE = os.environ['test_mode']

if __name__ == "__main__":
    app.debug = TEST_MODE
    PORT = 5000
    app.run(port=PORT)
    logging.basicConfig(filename='lyra.log', level=logging.DEBUG)