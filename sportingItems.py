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

engine = create_engine('sqlite:///ItemCatalog.db')
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
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
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

    # Create User in database if user does not exist already
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id
        
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

@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    f = open("accessToken.txt", 'w')
    f.write(access_token)
    f.close()
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        #return response
        return redirect(url_for('showLogin'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
    
def determineOriginatorOfContent(content):
    # Determine if given content is owned by user logged in. If not, return false, else true.
    if (getUserID(login_session['email']) != content.user_id):
        return False
    else:
        return True

def createUser(login_session):
    # Create new User from information in login_session object
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    # Return user object given user_id
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    # Return user_id given logged in user's email
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
    # Redirect user to login page if user not logged in
    if 'username' not in login_session:
        return redirect('/login')
    if request.method =='POST':
        #From the given information on newCategory.html, create and save the category in the database
        category = Categories(name = request.form['name'],
                              user_id = getUserID(login_session['email']))
        session.add(category)
        session.commit()
        category_id = session.query(Categories).filter_by(name = category.name).one().c_id
        return redirect(url_for('ShowCategories'))
    else:
        # If get request, redirect user to create new category
        return render_template('newCategory.html')
    
@app.route('/category/<int:category_id>/item/new',methods = ['GET','POST'])
def newItem(category_id):
    # Redirect user to login page if user not logged in
    if 'username' not in login_session:
        return redirect('/login')
    category_for_item = session.query(Categories).get(category_id)
    IsOriginatorOfContent = determineOriginatorOfContent(category_for_item)
    # If logged in user did not create category/item, alert the user with the appropriate warning/message
    if not IsOriginatorOfContent:
        return "<script>function myFunction() {alert('You are not authorized to create a new item in this category.');}</script><body onload='myFunction()''>"
    if request.method =='POST':
        # #From the given information on newItem.html, create and save the item in the database
        item = Items(name = request.form['name'],
                     description = request.form['description'],
                     category_id = category_id,
                     user_id = getUserID(login_session['email']))
        session.add(item)
        session.commit()
        return redirect(url_for('ShowItems', category_id = category_id))
    else:
        return render_template('newItem.html', category_id = category_id)
    
@app.route('/category/<int:category_id>/item',methods = ['GET'])    
def ShowItems(category_id):
    
    category = session.query(Categories).filter_by(c_id = category_id).one()
    items = session.query(Items).filter_by(category_id = category_id).all()
    IsOriginatorOfContent = determineOriginatorOfContent(category)
    #If user not logged in or if logged in user did not create item, redirect user to publicItems.html
    #where no option to add/edit/delete item is provided
    if 'username' not in login_session or not IsOriginatorOfContent:    
        return render_template('publicItems.html', items = items, category = category)
    else:
        return render_template('items.html', items = items, category = category)

@app.route('/category/<int:category_id>/item/<int:item_id>/edit',methods = ['GET','POST'])
def editItem(category_id, item_id):

    # Redirect user to login page if user not logged in
    if 'username' not in login_session:
        return redirect('/login')
    category_to_edit = session.query(Categories).get(category_id)
    item_to_edit = session.query(Items).get(item_id)
    IsOriginatorOfContent = determineOriginatorOfContent(item_to_edit)

    # If logged in user did not create category/item, alert the user with the appropriate warning/message
    if not IsOriginatorOfContent:
        return "<script>function myFunction() {if(confirm('You are not authorized to edit this item as this does not belong to you.')){return redirect(url_for('ShowCategories'));};}</script><body onload='myFunction()''>"
        #return "<script>function myFunction() {if(confirm('You are not authorized to edit this item as this does not belong to you.')){alert('thats great');};}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            item_to_edit.name = request.form['name']
        if request.form['description']:
            item_to_edit.description = request.form['description']
        session.commit()
        return redirect(url_for('ShowItems',category_id = category_id))
    else:
        return render_template('editItem.html',
                               category_id = category_id,
                               item_id = item_id,
                               item = item_to_edit)

@app.route('/category/<int:category_id>/item/<int:item_id>/delete',methods = ['GET','POST'])
def deleteItem(category_id, item_id):

    # Redirect user to login page if user not logged in
    if 'username' not in login_session:
        return redirect('/login')
    item_to_delete = session.query(Items).get(item_id)
    IsOriginatorOfContent = determineOriginatorOfContent(item_to_delete)
    # If logged in user did not create category/item, alert the user with the appropriate warning/message
    if not IsOriginatorOfContent:
        return "<script>function myFunction() {alert('You are not authorized to delete this item as this does not belong to you.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item_to_delete)
        session.commit()
        return redirect(url_for('ShowItems',category_id = category_id))
    else:
        return render_template('deleteItem.html', category_id = category_id, item_id = item_id, item = item_to_delete)
    
@app.route('/categories',methods = ['GET']) 
def ShowCategories():
    
    categories = session.query(Categories).all()
    #If user not logged in, redirect user to publicCategories.html
    #where no option to add/edit/delete category is provided
    if 'username' not in login_session:    
        return render_template('publicCategories.html', categories = categories)
    else:
        return render_template('categories.html', categories = categories)

@app.route('/category/<int:category_id>/edit',methods = ['GET','POST'])
def editCategory(category_id):

    # Redirect user to login page if user not logged in
    if 'username' not in login_session:
        return redirect('/login')
    category_to_edit = session.query(Categories).get(category_id)
    IsOriginatorOfContent = determineOriginatorOfContent(category_to_edit)
    # If logged in user did not create category, alert the user with the appropriate warning/message
    if not IsOriginatorOfContent:
        return "<script>function myFunction() {alert('You are not authorized to edit this category.');}</script><body onload='myFunction()''>"
    if request.method =='POST':
        category_name = request.form['name']
        category_to_edit.name = category_name
        session.commit()        
        return redirect(url_for('ShowCategories'))
    else:
        return render_template('editCategory.html',category = category_to_edit)

@app.route('/category/<int:category_id>/delete',methods = ['GET','POST'])
def deleteCategory(category_id):
    
    # Redirect user to login page if user not logged in
    if 'username' not in login_session:
        return redirect('/login')
    category_to_delete = session.query(Categories).filter_by(c_id=category_id).one()
    IsOriginatorOfContent = determineOriginatorOfContent(category_to_delete)
    # If logged in user did not create category, alert the user with the appropriate warning/message
    if not IsOriginatorOfContent:
        return "<script>function myFunction() {alert('You are not authorized to delete this category.');}</script><body onload='myFunction()''>"
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

