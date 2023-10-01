from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, DisplayUser, Addfeedbk


app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]="postgresql:///hashproject"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
app.config["SQLALCHEMY_ECHO"]=True
app.config["SECRET_KEY"]="Fooster23"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"]= False

connect_db(app)

toolbar=DebugToolbarExtension(app)

@app.route('/')
def home_page():
    return redirect('/register')

@app.route('/register', methods=['GET','POST'])
def register():
    """register form gets user information, checks to make sure username is available and then
    creates a new user object and sends it to the db"""
    form=RegisterForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        email=form.email.data
        first_name=form.first_name.data
        last_name=form.last_name.data
        checkUsers=User.query.filter(User.username==username)
        try:
         if checkUsers[0].username == username: 
          flash("User name alrady exists", 'danger')
          return redirect('/register')
        except:
         newUser=User.register(username=username, password=password,email=email,first_name=first_name, last_name=last_name )
        db.session.add(newUser)
        db.session.commit()
        session['user_id']= newUser.username
        session['fn']=newUser.first_name
        return redirect(f'users/{newUser.username}')
    if 'user_id' in session:
       flash('You are already registered!!', 'danger')
       return redirect(f'/users/{session["user_id"]}')
    else:
     return render_template('register.html', form = form)


@app.route('/users/<username>', methods=["GET","POST"])
def secret(username):  
    """get post route for the user.  validates the user has a password and logs them
    into the user display screen.  it also retrieves feedback the user has posted"""
    user=User.query.get(username)
    displayform=DisplayUser(obj = user)
    posts = Feedback.query.filter(Feedback.username==user.username)
    if session['user_id']==user.username:

     if displayform.validate_on_submit():
        return redirect('/')
     else:  
        flash(f"{session['fn']}'s super secret area...", 'success')
        return render_template('secret.html', user=user, form=displayform, posts=posts )
    else:
        flash('Please login if you want to get to the secret page', 'danger')
        
    return redirect('/login') 


@app.route('/login', methods=["GET","POST"])
def login():
    """logs in a user, validats if the user is already logged in and if so redirects them
    to user display screen"""
    form=LoginForm()
    if form.validate_on_submit():
      username=form.username.data
      password=form.password.data
      user=User.login(username=username, password=password)

      if user:
          
          flash(f"Welcome back, {user.username}", 'primary')
          session['user_id']=user.username
          session['fn']=user.first_name
        
          return redirect(f'/users/{user.username}')
      else:
          form.username.errors=['Invalid username/password']
    if 'user_id' in session:
       flash('You are already logged in!!', 'danger')
       return redirect(f'/users/{session["user_id"]}')
    else:      
     return render_template('login.html', form=form)

@app.route('/users/<username>/delete', methods=["POST"])
def deleteUser(username):
   """deltes a user, makes usre user is the user they are logged in as before they
   are abble to delete.  CASCASE ON is listed in the feedback model so they can be deleted even
   if they have feedback"""
   user=User.query.get(username)
   if session['user_id']==user.username:
      db.session.delete(user)
      db.session.commit()
      session.pop('user_id')
      session.pop('fn')

      return redirect('/')
   else:
      flash('you must be logged in to delete a user', 'danger')
      return redirect('/login')
   

@app.route('/users/<username>/feedback/add', methods=["GET","POST"])
def addfeedback(username):
   """validates correct user is logged in to make add a feedback under that username"""
   form=Addfeedbk()
   user=User.query.get(username)
   
   if session['user_id']==user.username:
      
     if form.validate_on_submit():
      title=form.title.data
      content=form.content.data
      newfeedback = Feedback(title=title, content=content, username=user.username)
      db.session.add(newfeedback)
      db.session.commit()
      return redirect(f'/users/{user.username}')
      
     return render_template('addfeedback.html', form=form, user=user)
   else:
      flash('get your ass back to login', 'danger')
      return redirect('/login')

@app.route('/feedback/<int:id>/update', methods=["GET","POST"])
def updatefeedback(id):
   """displays and updates feedback, validates user can do it"""
   feedback=Feedback.query.get(id)
   form= Addfeedbk(obj = feedback)
   if session['user_id']==feedback.username:
      if form.validate_on_submit():
         title=form.title.data
         content=form.content.data
         feedback.title=title
         feedback.content=content
         db.session.add(feedback)
         db.session.commit()
         return redirect(f'/users/{session["user_id"]}')
      
      return render_template('updatefeedback.html', form=form)
    
   else:
      flash("login before you can update feeedback", 'danger')
      return redirect('/login')  
      
@app.route('/feedback/<int:id>/delete')
def delfeedback(id):
   """deltes feedback, with user authorization"""
   feedback=Feedback.query.get(id)
   if session['user_id']==feedback.username:
      db.session.delete(feedback)
      db.session.commit()
      return redirect(f'/users/{session["user_id"]}')
   else:
      flash("You do not have permission to delet this post!", 'danger')
      return redirect(f'/users/{session["user_id"]}')
   
@app.route('/feedbackfeed/<int:id>/<returnpage>/delete')
def delfeedbackfeed(id, returnpage):
   """deletes feedback, with user authorization for feedback page
   I tried to also get it to work with the userpage but the routes are different"""
   feedback=Feedback.query.get(id)
   if session['user_id']==feedback.username:
      db.session.delete(feedback)
      db.session.commit()
      return redirect(f'/{returnpage}')
   else:
      flash("You do not have permission to delet this post!", 'danger')
      return redirect(f'/users/{session["user_id"]}')


@app.route('/feedback')
def feedback():
   """displays all feedback.  you don't need to be logged in to see it
   it validattes session[userid] on the form page to authorize
   user to edit or delete a feedback post"""
   feedback=Feedback.query.all()
   return render_template('feedback.html', feedback=feedback)


@app.route('/logout')
def logout():
    """logs out user, and pops their info out of session memeory"""
    session.pop('user_id')
    
    session.pop('fn')
    return redirect('/')
