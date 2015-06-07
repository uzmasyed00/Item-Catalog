from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, User

from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import AccessTokenCredentials
from oauth2client.client import FlowExchangeError

import random
import string


import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemCatalog"

engine = create_engine('sqlite:///Project3.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    print "authorization_code is ", code

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    print "access_token is", access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    print "url is", url
    h = httplib2.Http()
    print "h is", h

    print h.request(url, 'GET')[1]
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    #user = session.query(User).filter_by(email=login_session['email']).one()
    #return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE = state)

@app.route('/categories/JSON') 
def ShowCategoriesJSON():
    categories = session.query(Categories).all()
    return jsonify(categories= [c.serialize for c in categories])

@app.route('/category/<int:category_id>/item/JSON')
def ShowItemsJSON(category_id):
    items = session.query(Items).filter_by(category_id = category_id).all() 
    return jsonify(items= [i.serialize for i in items])
    
@app.route('/categories/new',methods = ['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method =='POST':
        category = Categories(name = request.form['name'])
        #print category
        session.add(category)
        session.commit()
        category_id = session.query(Categories).filter_by(name = category.name).one().c_id
        print "category_id is", category_id
        return redirect(url_for('ShowCategories'))
    else:
        return render_template('newCategory.html')
    
@app.route('/category/<int:category_id>/item/new',methods = ['GET','POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method =='POST':
        item = Items(name = request.form['name'],description = request.form['description'],category_id = category_id)
        session.add(item)
        session.commit()
        return redirect(url_for('ShowItems', category_id = category_id))
    else:
        return render_template('newItem.html')
    
@app.route('/category/<int:category_id>/item',methods = ['GET'])    
def ShowItems(category_id):
    print "I am inside ShowItems"
    category = session.query(Categories).filter_by(c_id = category_id).one()
    items = session.query(Items).filter_by(category_id = category_id).all()       
    return render_template('items.html', items = items, category = category)

@app.route('/category/<int:category_id>/item/<int:item_id>/edit',methods = ['GET','POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category_to_edit = session.query(Categories).get(category_id)
    item_to_edit = session.query(Items).get(item_id)
    if request.method == 'POST':
        if request.form['name']:
            item_to_edit.name = request.form['name']
        print "item_to_edit.name is ", item_to_edit.name
        if request.form['description']:
            item_to_edit.description = request.form['description']
        print "item_to_edit.description is ", item_to_edit.description
        session.commit()
        return redirect(url_for('ShowItems',category_id = category_id))
    else:
        return render_template('editItem.html', category_id = category_id, item_id = item_id, item = item_to_edit)

@app.route('/category/<int:category_id>/item/<int:item_id>/delete',methods = ['GET','POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item_to_delete = session.query(Items).get(item_id)
    if request.method == 'POST':
        session.delete(item_to_delete)
        session.commit()
        return redirect(url_for('ShowItems',category_id = category_id))
    else:
        return render_template('deleteItem.html', category_id = category_id, item_id = item_id)
    
@app.route('/categories',methods = ['GET']) 
def ShowCategories():
    categories = session.query(Categories).all()
    for category in categories:
        print category.name
    return render_template('categories.html', categories = categories)

@app.route('/category/<int:category_id>/edit',methods = ['GET','POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category_to_edit = session.query(Categories).get(category_id)
    if request.method =='POST':
        category_name = request.form['name']
        category_to_edit.name = category_name
        session.commit()        
        return redirect(url_for('ShowCategories'))
    else:
        return render_template('editCategory.html',category = category_to_edit)

@app.route('/category/<int:category_id>/delete',methods = ['GET','POST'])
def deleteCategory(category_id):
    #category_to_delete = session.query(Categories).get(category_id)
    if 'username' not in login_session:
        return redirect('/login')
    category_to_delete = session.query(Categories).filter_by(c_id=category_id).one()
    if request.method =='POST':        
        session.delete(category_to_delete)
        session.commit()
        return redirect(url_for('ShowCategories'))
    else:
        return render_template('deleteCategory.html',category = category_to_delete)

if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)

