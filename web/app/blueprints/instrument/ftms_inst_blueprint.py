
from flask import Blueprint, request
from flask_login import login_required

from app import db
from app.blueprints.auth_blueprint import check_user_group_access
from app.models.instrument import Instrument

ftms_instrument = Blueprint('ftms_instrument', __name__)


@ftms_instrument.route('/api/instrument/', methods=['POST'])
@login_required
def add_instrument():

    if check_user_group_access('admin'):

        new_instrument_data = request.get_json(silent=True)

        instrument = db.session.query(Instrument).filter_by('name' == new_instrument_data['name']).first()

        if not instrument:

            new_instrument = Instrument(new_instrument_data)
            db.session.add(new_instrument)
            db.session.commit()

            response_obj = {'status': 'success',
                                'message': 'user instrument {} successfully added'.format(new_instrument.name)
                            }

            return response_obj, 201

        else:

            response_obj = {'status': 'fail',
                            'message': 'Instrument with name: {} already exists'.format(new_instrument_data['name'])
                            }
            return response_obj, 409
        '''get instrument status
        '''
    else:

        response_obj = {'status': 'fail',
                        'message': 'Access Denied'
                        }

        return response_obj, 409

@ftms_instrument.route('/api/instrument/name/<name>', methods=['GET'])
@login_required
def get_instrument_by_name(name: str):

    instrument = db.session.query(Instrument).filter_by('name' == name).first()
    if instrument:
        return instrument.json(), 200
    else:
        return instrument_not_found(name)
    '''get instrument status
    '''

@ftms_instrument.route('/api/instrument/<int:id>', methods=['GET'])
@login_required
def get_instrument(_id):

    instrument = db.session.query(Instrument).filter_by('id' == _id).first()
    if instrument:
        return instrument.json(), 200
    else:
        return instrument_not_found(_id)

@ftms_instrument.route('/api/instrument/<id>/state', methods=['GET'])
@login_required
def get_instrument_state(_id: int):

    instrument = db.session.query(Instrument).filter_by('id' == _id).first()
    if instrument:

        response_obj = {'status': 'success',
                        'state': instrument.state
                        }

        return response_obj, 200

    else:

        return instrument_not_found(_id)

@ftms_instrument.route('/api/instrument/state/update', methods=['PUT'])
@login_required
def update_instrument_state():

    data = request.get_json()
    _id = data["instrument_id"]
    state = data["instrument_state"]

    instrument = db.session.query(Instrument).filter_by('id' == _id).first()

    if instrument:

        instrument.state = state
        db.session.commit()

        response_obj = {'status': 'success',
                        'message': 'Instrument {} state changed for {}'.format(instrument.name, instrument.state)
                        }

        return response_obj, 200

    else:

        return instrument_not_found(_id)

def instrument_not_found(arg):

    response_obj = {'status': 'fail',
                        'message': 'No instrument found for {}: {}'.format(arg.__name__, arg)
                    }

    return response_obj, 404
