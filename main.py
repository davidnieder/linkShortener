# _*_ coding: UTF-8 _*_

from flask import request, render_template, redirect, abort, g, jsonify
from flask import make_response 
from werkzeug.urls import iri_to_uri

from linkShortener import app

import hashlib, datetime, time, sqlite3

context = {
    'direct_redirect': True,
    'long_url': None,
    'short_url': None,
    'json': False
    }

@app.route('/', methods=['GET'])
def index():
    # redirect setting changed?
    if 'noredirect' in request.args:
        # set the cookie
        if request.args['noredirect'] == 'true':
            max_age = 60*60*24*356                  # about one year in seconds
            expire_date = datetime.date.today() + \
                          datetime.timedelta(356)   # one year in the future
            # convert to unix timestamp
            expire_date = time.mktime(expire_date.timetuple())

            # create response object with the cookie
            response = make_response(render_template('index.html', \
                                     direct_redirect=False))
            response.set_cookie('direct_redirect', value='false', \
                                max_age=max_age, expires=expire_date)
            return response
        # remove the cookie
        elif request.args['noredirect'] == 'false':
            expire_date = datetime.date.today() + \
                          datetime.timedelta(-1)   # yesterday
            expire_date = time.mktime(expire_date.timetuple())

            # set a cookie which expires in the past
            response = make_response(render_template('index.html', \
                                     direct_redirect=True))
            response.set_cookie('direct_redirect', expires=expire_date)

            return response            

    # new entry?
    elif 'longurl' in request.args:
        context['long_url'] = request.args['longurl']
        if validate_url():
            # generate a short identifier with md5
            md5_hash = hashlib.md5(context['long_url'])
            context['short_url'] = md5_hash.hexdigest()[:5]
            write_new_entry()

            # return json?
            if context['json'] == True:
                return jsonify(long_url=context['long_url'], short_url= \
                               request.url_root + context['short_url'])

            return render_template('new.html', long_url=context['long_url'], \
                                   short_url=request.url_root + context['short_url'])
        else:
            if context['json'] == True:
                return jsonify(error='could not parse url')

            return render_template('index.html', error='bad_url', \
                                   long_url=context['long_url'], \
				   direct_redirect=context['direct_redirect'])

    return render_template('index.html', direct_redirect=context['direct_redirect'])

@app.route('/<id>/', methods=['GET'])
def short_url(id):
    context['short_url'] = id
    get_long_url()

    if context['long_url']:
        if context['json'] == True:
            return jsonify(long_url=context['long_url'], short_url= \
                           request.url_root + context['short_url'])

        if context['direct_redirect']:
            return redirect(iri_to_uri(context['long_url']))
        else:
            return render_template('show.html', long_url=context['long_url'], \
                                   short_url=request.url_root+context['short_url'])
    else:
        if context['json'] == True:
            return jsonify(error='404')
        abort(404)

def get_long_url():
    cursor = g.db.execute('SELECT long_url FROM urls WHERE short_url=\'%s\'' \
                          %(context['short_url']))
    long_url = cursor.fetchone()
    if long_url:
        context['long_url'] = long_url[0]
    else:
        context['long_url'] = None

def write_new_entry():
    # check first if there is an corresponding entry
    cursor = g.db.execute('SELECT long_url FROM urls WHERE long_url=\'%s\'' \
                          %(context['long_url']))
    if cursor.fetchone():
        return
    # write new entry
    g.db.execute('INSERT INTO urls (long_url, short_url) values (?,?)',
                 [context['long_url'], context['short_url']])
    g.db.commit()

def validate_url():
    # haha
    return True

@app.before_request
def check_for_cookie():
    # if the cookie exists set 'direct_redirect' to False
    if 'direct_redirect' in request.cookies:
        context['direct_redirect'] = False
    else:
        context['direct_redirect'] = True

@app.before_request
def return_json():
    if 'json' in request.args:
        if request.args['json'] == 'true':
            context['json'] = True
        else:
            context['json'] = False
    else:
        context['json'] = False

@app.before_request
def open_db():
    g.db = sqlite3.connect(app.root_path + '/url_db.sqlite3')

@app.teardown_request
def close_db(exception):
    g.db.close()

