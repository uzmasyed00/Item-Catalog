from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items

engine = create_engine('sqlite:///Project3.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/categories/new',methods = ['GET','POST'])
def CategoriesNew():
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
    if request.method =='POST':
        item = Items(name = request.form['name'],description = request.form['description'],category_id = category_id)
        session.add(item)
        session.commit()
        return render_template('ItemCreated.html')
    else:
        return render_template('newItem.html')
    
@app.route('/category/<int:category_id>/item',methods = ['GET'])    
def ShowItems(category_id):
    print "I am inside ShowItems"
    category = session.query(Categories).filter_by(c_id = category_id).one()
    items = session.query(Items).filter_by(category_id = category_id).all()
    #if request.method == 'POST':        
    for item in items:
        print item.name
        #return render_template('newItem.html')
    #else:
    return render_template('items.html', items = items, category = category)

@app.route('/category/<int:category_id>/item/<int:item_id>/edit',methods = ['GET','POST'])
def editItem(category_id, item_id):
    category_to_edit = session.query(Categories).get(category_id)
    item_to_edit = session.query(Items).get(item_id)
    if request.method == 'POST':
        item_to_edit.name = request.form['name']
        print "item_to_edit.name is ", item_to_edit.name
        item_to_edit.description = request.form['description']
        print "item_to_edit.description is ", item_to_edit.description
        #session.add(item_to_edit)
        session.commit()
        return redirect(url_for('ShowItems',category_id = category_id))
    else:
        return render_template('editItem.html', category_id = category_id, item_id = item_id)
        #return render_template('editItem.html', category_to_edit, item_to_edit)

@app.route('/category/<int:category_id>/item/<int:item_id>/delete',methods = ['GET','POST'])
def deleteItem(category_id, item_id):
    print "I am going to delete the item"
    
@app.route('/categories',methods = ['GET']) 
def ShowCategories():
    categories = session.query(Categories).all()
    #for category in categories:
        #print category.name
    return render_template('categories.html', categories = categories)

@app.route('/category/<int:category_id>/edit',methods = ['GET','POST'])
def editCategory(category_id):
    #isnt category_id defined as c_id, then how is it accepting category_id?
    category_to_edit = session.query(Categories).get(category_id)
    #print "category_name to be edited is",category_to_edit
    if request.method =='POST':
        category_name = request.form['name']
        category_to_edit.name = category_name
        session.commit()        
        return redirect(url_for('ShowCategories'))
    else:
        #return render_template('editCategory.html', category =category_to_edit)
        #print "I am going to render editCategory.html"
        return render_template('editCategory.html',category = category_to_edit)

@app.route('/category/<int:category_id>/delete',methods = ['GET','POST'])
def deleteCategory(category_id):
    category_to_delete = session.query(Categories).get(category_id)
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

