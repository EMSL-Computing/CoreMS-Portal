from app import db
from flask import current_app

class Instrument(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    state = db.Column(db.String(100), default='idle')

    def json(self):
        return {'id:': self.id, 'name': self.name, 'state': self.state}

@db.event.listens_for(Instrument.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
    instruments = ["12T_FTICRMS", "15T_FTICRMS", "21T_FTICRMS"]
    for instrument_name in instruments:
        instrument = Instrument(name=instrument_name)
        db.session.add(instrument)
    db.session.commit()
