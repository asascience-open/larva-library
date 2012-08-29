from tests.flask_mongo import FlaskMongoTestCase
from StringIO import StringIO

class LibraryTestCase(FlaskMongoTestCase):

    def test_import_json(self):

        jsonstr = """
        {
          "results": [
            {
              "status": "public", 
              "name": "1", 
              "created": 1344460387672, 
              "geometry": "POLYGON ((153.2746875000000273 25.7885529585785953, -67.8581249999999727 27.9832813434000016, -67.8581249999999727 53.5328232787000005, -117.4284374999999727 67.0625260424999965, 138.5090625000000273 51.8279954420795335, 153.2746875000000273 25.7885529585785953))", 
              "geo_keywords": [
                "1"
              ], 
              "keywords": [
                "1"
              ], 
              "user": "wilcox.kyle@gmail.com", 
              "common_name": "1", 
              "genus": "", 
              "notes": "1", 
              "species": "", 
              "lifestages": [
                {
                  "name": "first", 
                  "linear_b": null, 
                  "notes": "", 
                  "linear_a": null, 
                  "duration": 1,
                  "settlement": null,
                  "capability": {
                    "nonswim_turning": "random", 
                    "variance": 0.0, 
                    "swim_turning": "random", 
                    "vss": 0.005
                  },
                  "diel": [
                    {
                      "plus_or_minus": "-", 
                      "min": 1.0, 
                      "max": 40.0, 
                      "hours": 1, 
                      "time": null, 
                      "type": "cycles", 
                      "cycle": "sunrise"
                    },
                    {
                      "plus_or_minus": "+", 
                      "min": 100.0, 
                      "max": 120.0, 
                      "hours": 1, 
                      "time": null, 
                      "type": "cycles", 
                      "cycle": "sunset"
                    }
                  ], 
                  "taxis": [
                    {
                      "min": 30.0, 
                      "gradient": 8.0, 
                      "max": 40.0, 
                      "variable": "sea_water_temperature", 
                      "units": "\u00b0C"
                    },
                    {
                      "min": 30.0, 
                      "gradient": 8.0, 
                      "max": 50.0, 
                      "variable": "sea_water_salinity", 
                      "units": "PSU"
                    }
                  ]
                },
                {
                  "name": "second", 
                  "linear_b": null, 
                  "notes": "", 
                  "linear_a": null, 
                  "duration": 2,
                  "settlement": null,
                  "capability": {
                    "nonswim_turning": "random", 
                    "variance": 0.005, 
                    "swim_turning": "random", 
                    "vss": 0.01
                  },
                  "diel": [
                    {
                      "plus_or_minus": "-", 
                      "min": 40.0, 
                      "max": 60.0, 
                      "hours": 1, 
                      "time": null, 
                      "type": "cycles", 
                      "cycle": "sunrise"
                    },
                    {
                      "plus_or_minus": "+", 
                      "min": 80.0, 
                      "max": 100.0, 
                      "hours": 1, 
                      "time": null, 
                      "type": "cycles", 
                      "cycle": "sunset"
                    }
                  ], 
                  "taxis": [
                    {
                      "min": 30.0, 
                      "gradient": 8.0, 
                      "max": 40.0, 
                      "variable": "sea_water_temperature", 
                      "units": "\u00b0C"
                    },
                    {
                      "min": 30.0, 
                      "gradient": 8.0, 
                      "max": 50.0, 
                      "variable": "sea_water_salinity", 
                      "units": "PSU"
                    }
                  ]
                }
              ]
            }
          ]
        }
        """

        # Import JSON surface
        rv = self.app.post('/library/import.json',
                data={ 'jsonfile': (StringIO(jsonstr), 'json_file.json')}
            )
        print rv