from larva_library.models.user import User
from larva_library.models.library import Library
from larva_library.models.lifestage import LifeStage
from larva_library.models.diel import Diel
from larva_library.models.taxis import Taxis
from larva_library.models.capability import Capability
from larva_library.models.settlement import Settlement

def remove_mongo_keys(d):

    remove_keys = ['_id', '_collection', '_database', '_keywords']

    if d is not None:
        if isinstance(d, list):
            for sublist in d:
                remove_mongo_keys(sublist)
        elif isinstance(d, dict):
            for key in d.keys():
                try:
                    remove_keys.index(key)
                    del(d[key])
                except:
                    remove_mongo_keys(d[key])

    return
