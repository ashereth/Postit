import functools
import uuid
from datetime import datetime
from dataclasses import asdict
from passlib.hash import pbkdf2_sha256
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
    request,
)
from postit.forms import PostForm, RegisterForm, LoginForm
from postit.models import Post, Account
pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)

#base explore page that shows all posts
@pages.route("/")
def index():
    #get all the posts data from db 
    posts_data = current_app.db.posts.find({})
    #create a list of Post objects using the posts_data
    posts = (Post(**post) for post in reversed(list(posts_data)))
    return render_template(
        "index.html",
        title="Postit", posts=posts
    )

#page to make a new post
@pages.route("/add_post", methods=["GET", "POST"])
def add_post():
    #create the form for the post
    form = PostForm()
    if form.validate_on_submit():
        #create the post using the data from the form
        post = Post(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            body=form.body.data,
            date=datetime.now().strftime("%m/%d/%Y"),
            account=session["username"]
        )
        #add the post to the database
        current_app.db.posts.insert_one(asdict(post))

        #add post to active accounts list of posts
        current_app.db.accounts.update_one(
            {"_id": session["user_id"]}, {"$push": {"posts": post._id}}
        )

        return redirect(url_for(".index"))
    return render_template("add_post.html", title="Posts - New Post", form=form)



#route to show users their account page
@pages.route("/account")
def account():
    #get account data and make an account object with the data
    account_data = current_app.db.accounts.find_one({"email": session["email"]})
    account = Account(**account_data)

    #get all the posts from this account and make a list of them
    post_data = current_app.db.posts.find({"_id": {"$in": account.posts}})
    posts = [Post(**post) for post in post_data]

    return render_template(
        "account.html",
        title="Account", 
        posts=posts,
        username=session["username"],
        account=account
        )


#route for looking at other people accounts
@pages.route("/other_account/<string:account>")
def other_account(account):
    #get the current user
    current_user_data = current_app.db.accounts.find_one({"username": session["username"]})
    current_user = Account(**current_user_data)
    #get the account that was clicked on
    account_data = current_app.db.accounts.find_one({"username": account})
    _account = Account(**account_data)

    #get all the posts from this account and make a list of them
    post_data = current_app.db.posts.find({"_id": {"$in": _account.posts}})
    posts = [Post(**post) for post in post_data]

    print(current_user)
    return render_template(
        "other_account.html",
        title="Account", 
        posts=posts,
        username=_account.username,
        current_user=current_user,
        _account=_account
        )



#function for liking posts
@pages.route("/like_post/<post_id>")
def like_post(post_id):
    #get the post data from database
    post = current_app.db.posts.find_one({"_id": post_id})
    #if the post exists
    if post:
        #if the post hasnt been liked by current user like it
        if (session["username"] not in post["liked_by"]):
            post["likes"] += 1
            current_app.db.posts.update_one({"_id": post_id}, {"$set": {"likes": post["likes"]}})
            current_app.db.posts.update_one(
                {"_id": post_id}, 
                {"$push": {"liked_by": session["username"]}})
        #if post has been liked by current user unlike it
        else:
            post["likes"] -= 1
            current_app.db.posts.update_one({"_id": post_id}, {"$set": {"likes": post["likes"]}})
            current_app.db.posts.update_one(
                {"_id": post_id}, 
                {"$pull": {"liked_by": session["username"]}})
    return redirect(url_for(".index"))
    

#follow an account
@pages.route("/follow/<account>")
def follow(account):
    #get current user
    current_user_data = current_app.db.accounts.find_one({"username": session["username"]})
    current_user = Account(**current_user_data)
    #get the account that was clicked on
    account_data = current_app.db.accounts.find_one({"username": account})
    _account = Account(**account_data)

    #get all the posts from this account and make a list of them
    post_data = current_app.db.posts.find({"_id": {"$in": _account.posts}})
    posts = [Post(**post) for post in post_data]

    # add current user to accounts followers
    current_app.db.accounts.update_one({"_id": _account._id}, {"$push": {"follower": current_user.username}})
    # add account to current users list of account that they are following
    current_app.db.accounts.update_one({"_id": current_user._id}, {"$push": {"following": _account.username}})
    return redirect(url_for(".other_account", 
                           title="Account", 
                            posts=posts,
                            account=_account.username,
                            username=_account.username,
                            current_user=current_user)
                    )


#unfollow an account
@pages.route("/unfollow/<account>")
def unfollow(account):
    #get current user
    current_user_data = current_app.db.accounts.find_one({"username": session["username"]})
    current_user = Account(**current_user_data)
    #get the account that was clicked on
    account_data = current_app.db.accounts.find_one({"username": account})
    _account = Account(**account_data)

    #get all the posts from this account and make a list of them
    post_data = current_app.db.posts.find({"_id": {"$in": _account.posts}})
    posts = [Post(**post) for post in post_data]

    #remove current user from accounts followers
    current_app.db.accounts.update_one({"_id": _account._id}, {"$pull": {"follower": current_user.username}})
    #remove account from current users list of accounts that they are following
    current_app.db.accounts.update_one({"_id": current_user._id}, {"$pull": {"following": _account.username}})
    return redirect(url_for(".other_account", 
                           title="Account", 
                            posts=posts,
                            account=_account.username,
                            username=_account.username,
                            current_user=current_user)
                    )




"""
Below are routes for registering and logging in
"""
#route for creating an account
@pages.route("/register", methods=["POST", "GET"])
def register():
    #if session already has a logged in email redirect to base route
    if session.get("email"):
        return redirect(url_for(".index"))

    form = RegisterForm()
    #if form is submitted and validated then get the data from it and save it as account
    if form.validate_on_submit():
        account = Account(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            username=form.username.data,
            password=pbkdf2_sha256.hash(form.password.data),
        )
        #add account to database of accounts
        current_app.db.accounts.insert_one(asdict(account))
        #flash a success message
        flash("Account created successfully", "success")
        #redirect user to login page
        return redirect(url_for(".login"))

    return render_template(
        "register.html", title="Movies Watchlist - Register", form=form
    )

#route for logging in
@pages.route("/login", methods=["GET", "POST"])
def login():
    #if user is already signed in redirect to base
    if session.get("email"):
        return redirect(url_for(".index"))
    #create form and check validation
    form = LoginForm()

    if form.validate_on_submit():
        #try to find the account in the db using the email from the form
        account_data = current_app.db.accounts.find_one({"email": form.email.data})
        #if couldnt find account_data using the email flash message
        if not account_data:
            flash("Login credentials not correct", category="danger")
            return redirect(url_for(".login"))
        #create a account object
        account = Account(**account_data)
        # check if the form password equals the user password
        if account and pbkdf2_sha256.verify(form.password.data, account.password):
            #populate the session with anything that we need and redirect to base
            session["user_id"] = account._id
            session["email"] = account.email
            session["username"] = account.username

            return redirect(url_for(".index"))

        flash("Login credentials not correct", category="danger")
    #if account couldnt be verified return to login page
    return render_template("login.html", title="Movies Watchlist - Login", form=form)


#logout route
@pages.route("/logout")
def logout():
    del session["email"]
    del session["user_id"]
    del session["username"]

    return redirect(url_for(".login"))