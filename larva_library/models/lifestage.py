from mongokit import Document
from larva_library import db
from larva_library.models.diel import Diel
from larva_library.models.taxis import Taxis
from larva_library.models.capability import Capability
from wtforms import *

class LifeStage(Document):
    __collection__= 'lifestage'
    use_dot_notation = True
    use_autorefs = True
    structure = {
        'name'      : unicode,
        'duration'  : int,
        'linear_a'  : float,
        'linear_b'  : float,
        'diel'      : [Diel],
        'taxis'     : [Taxis],
        'capability': Capability,
        'notes'     : unicode
    }
db.register([LifeStage])

class LifeStageWizard(Form):
    name = TextField('Name')
    duration = IntegerField('Lifestage Duration (days)')
    linear = BooleanField("")
    linear_a = FloatField("A", [validators.optional()])
    linear_b = FloatField("B", [validators.optional()])
    notes = TextAreaField('Notes')

    diel = BooleanField('Diel')
    taxis = BooleanField('Sensory')
    capability = BooleanField('Capability')

    # Diel
    diel_hours = FloatField("", [validators.optional()])
    diel_min_depth = FloatField("Min", [validators.optional()])
    diel_max_depth = FloatField("Max", [validators.optional()])
    diel_data = HiddenField('diel_data')

    # Capability
    vss = FloatField('Vertical Swimming Speed (m/s)')
    variance = FloatField('Swimming Speed Variance (m/s)', default=0)
    swim_turning = RadioField("", [validators.optional()], choices=[('reverse', 'Reverses swimming direction'), ('random', 'Random selection of swimming direction')])
    nonswim_turning = RadioField("", [validators.optional()], choices=[('random', 'Random selection of swimming direction'), ('downward', 'Always swim downward'), ('upward', 'Always swim updard')])

    # Taxis
    variable = SelectField('Variable', [validators.optional()], choices=[('sea_water_salinity', 'Salinity (PSU)'), ('sea_water_temperature', 'Temperature (deg C)')])
    taxis_min = FloatField("Min", [validators.optional()])
    taxis_max = FloatField("Max", [validators.optional()])
    taxis_grad = FloatField("Sensory Gradient +/-", [validators.optional()])
    taxis_data = HiddenField('taxis_data')