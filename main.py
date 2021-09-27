import sys, json, logging, os
from os.path import join, dirname


from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
import flask
import requests

import service


app = Flask(__name__)

load_dotenv(".env")

try:
    variables_model = service.read_yaml('./model.yaml')
except FileNotFoundError:
    app.logger.warning("Configuration files, not founded.")
    pass

transactional_parameters = variables_model['transactionalParameters']

transactional_parameters.pop('subMerchantDetails')
#transactional_parameters.pop('transactionOptions')


@app.route("/", methods=['GET'])
def index():
    if len(request.args) != 0:
        return render_template('index.html', form=service.assign_parameters(transactional_parameters))

    return redirect('/?' + service.url_parser(transactional_parameters))


@app.route("/health", methods=['GET'])
def get_health_status():
    from flask import jsonify
    return jsonify({
        "status": 200,
        "message": "Everything is ok."
    })


@app.route("/get-embedded", methods=['GET'])
def get_embedded():
    """
    '/get-embedded' will load the embedded form, passing the form_token as a url parameter
    """
    form_token = request.args.get('form-token')
    return render_template(
        'embedded_form.html', 
        rest_static_url=os.environ['rest_static_url'],
        kr_public_key=os.environ['test_public_key'] if os.environ['test_mode'] else os.environ['prod_public_key'],
        kr_popin=True if request.form.get('kr-popin') else False,
        formToken=form_token, 
    )


@app.route("/get-form-token", methods=['POST'])
def get_form_token():
    """
    '/get-form-token' will only generate the form token
    """
    api_url = request.form.get('rest_api_server_name') if request.form.get('rest_api_server_name') is None else os.environ['rest_api_server_name']
    send_body = service.new_body_to_send(transactional_parameters)

    CONTRIB = f"API - Python_Flask_Embedded_Examples_2.x_1.0.0/{flask.__version__}/{sys.version[:5]}"
    send_body['contrib'] = CONTRIB

    app.logger.info(json.dumps(send_body, indent=4))
    form_token = create_form_token(json.dumps(send_body), api_url)
    return form_token


@app.route("/transaction-success", methods=['GET'])
def transaction_success():
    return render_template(
        'loading_screen.html'
    )


@app.route("/transaction-refused", methods=['GET'])
def transaction_refused():
    pass


@app.route("/embedded-form", methods=['POST'])
def embedded_form():
    """
    Will create the form_token and load the embedded form at the same time
    """
    api_url = os.environ['rest_server_api_url']
    send_body = service.new_body_to_send(transactional_parameters)

    CONTRIB = f"Python_Flask_Embedded_Examples_2.x_1.0.0/{flask.__version__}/{sys.version[:5]}"
    send_body['contrib'] = CONTRIB

    app.logger.info(json.dumps(send_body, indent=4))
    form_token = create_form_token(json.dumps(send_body), api_url)

    if form_token == None:
        return render_template('error.html')

    return render_template(
        'embedded_form.html', 
        rest_static_url=os.environ['rest_static_url'],
        kr_public_key=os.environ['test_public_key'] if os.environ['test_mode'] else os.environ['prod_public_key'],
        kr_popin=True if request.form.get('kr-popin') else False,
        formToken=form_token, 
    )


@app.route('/capture-ipn', methods=['GET','POST'])
def capture_ipn():
    """
    Endpoint to capture the transaction ipn
    """
    if request.form.get('kr-answer') == None:
        return "KO - Invalid request.", 400

    app.logger.info(json.dumps(json.loads(request.form.get('kr-answer').replace('"', '\"')), indent=4))
    signature = service.compute_hmac_sha256_signature(
        os.environ['test_password'] if os.environ['test_mode'] else os.environ['prod_password'],
        request.form.get('kr-answer')
    )
    if signature != request.form.get('kr-hash'):
        return "KO - Signatures does not match.", 401

    # Check in your DB if the transaction was already processed
    return "OK - Successful transaction payment.", 200


@app.route('/redirect', methods=['POST'])
def redirect_():
    """
    Redirect will proceed with the payment, and will either succeed or refused the payment.
    """
    if request.args.get('status') == 'success':
        signature = service.compute_hmac_sha256_signature(
            os.environ['test_hmac_sha_256_key'] if os.environ['test_mode'] else os.environ['prod_hmac_sha_256_key'],
            request.form.get('kr-answer')
        )
        app.logger.info(json.dumps(json.loads(request.form.get('kr-answer').replace('"', '\"')),indent=4))

        return render_template(
            'redirect.html',
            redirect_obj=request.form,
            signature=signature,
            signature_validation=True if signature == request.form.get('kr-hash') else False,
            kr_answer=json.dumps(json.loads(request.form['kr-answer']), indent=4)
        )
    if request.args.get('status') == 'refused':
        return "Payment decline, exceded retrys attempts."


def create_form_token(entry_body, url=None):
    """
    Create form token to load the payment method
    """
    shop_id = os.environ['shop_id']
    password = os.environ['test_password'] if os.environ['test_mode'] else os.environ['prod_password']
    string_to_encode = f"{shop_id}:{password}"

    if url == None:
        create_payment_url = f"{os.environ['rest_server_api_url']}V4/Charge/CreatePayment"
    else:
        create_payment_url = f"{url}V4/Charge/CreatePayment"

    get_encoder = service.encode_to_base64(string_to_encode)
    set_header = {"Authorization": f"Basic {get_encoder}"}
    try:
        form_token = json.loads(requests.post(
            create_payment_url, data=entry_body, headers=set_header
        ).text)['answer']['formToken']
        return form_token
    except ValueError:
        pass
