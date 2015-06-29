# Item-Catalog

Install Git, Vagrant and Virtual Box. 
From the terminal, run “git clone http://github.com/udacity/fullstack-nanodegree-vm fullstack”. This will give you a directory named fullstack.
In the terminal, navigate to fullstack/vagrant/catalog and clone the https://github.com/uzmasyed00/Item-Catalog repository in the working directory
Using the terminal, change directory to fullstack/vagrant (cd fullstack/vagrant), then type vagrant up to launch your virtual machine followed by "vagrant ssh". 
Change directory into /vagrant/catalog/Item-Catalog directory where you will find the following files/folders:
Folders:
Static
Templates
Files:
accessToken.txt
client_secrets.json
database_setup.py
       sportingItems.py
While in the working directory, run database_setup.py by typing “python database_setup.py”. This will generate a database_setup.pyc file in the working directory.
Next, type “python sportingItems.py”. Running this command will start the webserver on port 8000 on your local machine.
Now, in a browser of your choice, type the following URL:
http://localhost:8000/categories
Click the login link which will direct you to a sign-in page.
Press the sign-in button to sign in to the application with your Gmail address.
Once logged in, hit the “Create a new Category” link, fill out the category information and press the Create button. This will save the category in the database. You can click “Cancel” any time to cancel creation of a new category.
You can also edit and delete the category by pressing the “Edit Category” and “Delete Category” links on the categories page respectively.
Click on the created category if you want to see items belonging to that category. You can then click the “Add item” link to add new items for that category.
You can also edit and delete the item by pressing the “Edit Item” and “Delete Item” links on the items page respectively.
However, it must be noted that you can only add/edit/delete items for a category that was created by you. If someone else created the category you are trying to add items to or edit/delete items within, then you will be prevented from adding/editing/deleting any items in that category.
Clicking on “Home” will redirect you back to the categories page and clicking on “Logout” will log you out of the web application.
If you are logged out of the web application, you will not be able to add/edit/delete any category or item in the web application.




