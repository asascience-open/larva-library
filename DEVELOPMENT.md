## Development Environment

Assumes you have:
* python >= 2.7.2
* MongoDB >= 1.8.2
* foreman (ruby gem)
* heroku (ruby gem)

### Install the requirements
    `$ pip install -r requirements.rb`

### Create an .env file with the following contents
    `APPLICATION_SETTINGS=development.py`
    `SECRET_KEY=`
    `FACEBOOK_APP_ID=`
    `FACEBOOK_APP_SECRET=`
    `GOOGLE_CLIENT_SECRET=`
    `GOOGLE_CLIENT_ID=`

### Edit larva_library/development.py
    `Add MongoDB connection information`

### Start the local server
    `$ foreman start`


## Starting a Heroku instance

    `$ heroku create --stack cedar larva_library`

    `$ heroku config:add APPLICATION_SETTINGS=production.py`
    `$ heroku config:add SECRET_KEY=somethinglongandunique`
    `$ heroku config:add FACEBOOK_APP_ID=aaa`
    `$ heroku config:add FACEBOOK_APP_SECRET=bbb`
    `$ heroku config:add GOOGLE_CLIENT_ID=ccc`
    `$ heroku config:add GOOGLE_CLIENT_SECRET=ddd`

    `$ heroku addons:add mongolab:starter`
    `$ git push heroku master`
    `$ heroku ps:scale web=1`
