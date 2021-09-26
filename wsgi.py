import os, logging
from main import app
# from dotenv import load_dotenv, dotenv_values

# load_dotenv('.env')


if __name__ == "__main__":
    app.debug=True
    app.run()
    logging.basicConfig(filename='lyra.log', level=logging.DEBUG)
