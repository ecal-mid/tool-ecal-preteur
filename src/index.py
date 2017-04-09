""" Index """

from flask import Blueprint, render_template, jsonify, request
from itsdangerous import URLSafeSerializer

import os
import cloudstorage as gcs
import base64
import re
import time
import datetime
from google.appengine.api import app_identity
from google.appengine.ext import ndb

from .models import Loan

bp = Blueprint(
    'index', __name__,
    static_folder='../static',
    template_folder='../templates')

ancestor_key = ndb.Key('Loan', '2016-2017')


def upload_file(file_name, file_data, loaner):
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    file_name = '/' + bucket_name + '/' + file_name
    gcs_file = gcs.open(file_name,
                        'w',
                        content_type='image/png',
                        options={'x-goog-acl': 'public-read',
                                 'x-goog-meta-loaner': loaner},
                        retry_params=write_retry_params)
    gcs_file.write(file_data)
    gcs_file.close()
    return file_name


@bp.route('/')
def index():
    """Return the homepage."""
    return render_template('index.html')


@bp.route('/loans')
def list_loans():
    """Return the list of loans."""
    loans = Loan.query(Loan.date_out == None, ancestor=ancestor_key).order(-Loan.date_in).fetch()
    prefix = 'https://storage.googleapis.com'
    is_prod = os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/')
    if not is_prod:
        prefix = 'http://localhost:8080/_ah/gcs'
    return render_template('loans.html', loans=loans, prefix=prefix)


@bp.route('/loans', methods=['POST'])
def create_loan():
    """Records a new loan."""
    loaner = request.form['loaner']
    item = request.form['item']
    item_id = None
    if item[:2] == 'g-':
        print('saving generic item: ' + item)
        item_id = item
    else:
        image_b64 = item
        img_data = re.sub('^data:image/.+;base64,', '', image_b64).decode('base64')
        filename = time.strftime("%Y%m%d-%H%M%S") + '-' + loaner
        file_id = upload_file(filename, img_data, filename)
        item_id = file_id
    # save entry to datastore
    loan = Loan(parent=ancestor_key)
    loan.loaner = loaner
    loan.photo = item_id
    loan.date_in = datetime.datetime.now()
    loan.date_out = None
    loan.put()
    return 'Success'


@bp.route('/loans/validate/<int:id>', methods=['POST'])
def validate_loan(id):
    """Validate a loan."""
    loan = Loan.get_by_id(id, parent=ancestor_key)
    loan.date_out = datetime.datetime.now()
    loan.put()
    return 'Success'


@bp.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
