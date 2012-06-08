## Development Environment

Assumes you have:
* python >= 2.7.2
* MongoDB >= 1.8.2
* foreman (ruby gem)
* heroku (ruby gem)

### Install the requirements
    $ pip install -r requirements.rb

### Create an .env file with the following contents
    APPLICATION_SETTINGS=development.py
    SECRET_KEY=
    FACEBOOK_APP_ID=
    FACEBOOK_APP_SECRET=
    GOOGLE_CLIENT_SECRET=
    GOOGLE_CLIENT_ID=

### Edit larva_library/development.py
    Add MongoDB connection information

### Start the local server
    $ foreman start


## Starting a Heroku instance
    Custom buildpack for GEOS: https://github.com/cirlabs/heroku-buildpack-geodjango

    $ heroku create --stack cedar --buildpack http://github.com/cirlabs/heroku-buildpack-geodjango NAME_OF_APP`

    $ heroku config:add APPLICATION_SETTINGS=production.py
    $ heroku config:add SECRET_KEY=somethinglongandunique
    $ heroku config:add FACEBOOK_APP_ID=aaa
    $ heroku config:add FACEBOOK_APP_SECRET=bbb
    $ heroku config:add GOOGLE_CLIENT_ID=ccc
    $ heroku config:add GOOGLE_CLIENT_SECRET=ddd
    $ heroku config:add GEOS_LIBRARY_PATH='/app/.geodjango/geos/lib/libgeos_c.so'
    $ heroku config:add GDAL_LIBRARY_PATH='/app/.geodjango/gdal/lib/libgdal.so'

    $ heroku addons:add mongolab:starter
    $ git push heroku master
    $ heroku ps:scale web=1
