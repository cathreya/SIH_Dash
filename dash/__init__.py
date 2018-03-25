from flask import Flask, json, request, render_template, jsonify
from flask_twitter_oembedder import TwitterOEmbedder
from random import shuffle
from flask_cache import Cache
import tweepy
import time
import atexit
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

auth = tweepy.OAuthHandler(app.config['TWITTER_CONSUMER_KEY'],
                           app.config['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(app.config['TWITTER_ACCESS_TOKEN'],
                      app.config['TWITTER_ACCESS_TOKEN_SECRET'])
tweepy_api = tweepy.API(auth)

cache = Cache(app,config={'CACHE_TYPE': 'simple'})
tweetEmbedder = TwitterOEmbedder(app,cache,100)


# accounts = ["HRDMinistry","PMOindia","FinMinIndia","HMOIndia"
# ,"ReutersTech","TechCrunch","Variety","THR","DEADLINE"]

accounts = ["IndiaToday", "TimesNow", "ndtv", "htTweets", "CNNnews18", "timesofindia", "the_hindu", "abpnewstv", "IndianExpress", "ZeeNews", "aajtak", "DDNewsLive"]
currentlyDisplayed = 0
# THIS PART HANDLES THE DB CONFIGURATION
class Tweet(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	tweetID = db.Column(db.Integer, index=True, unique=True)
	time = db.Column(db.DateTime(timezone=False), index=True, default = datetime.utcnow)
	
	def __repr__(self):
		return '<Tweet ID {} Time {}>'.format(self.tweetID,self.time)    



def getTweets(username):
	tweets = tweepy_api.user_timeline(screen_name = username, count=2)
	# for t in tweets:
	# 	returnList.append({"tweet":t.text,
	# 						"created_at":t.created_at,
	# 						"username":username,
	# 						"headshot_url":t.user.profile_image_url
	# 					})
	for tweet in tweets:
		t = Tweet(tweetID=tweet.id)
		if Tweet.query.filter_by(tweetID = tweet.id) == None:
			db.session.add(t)
			


	db.session.commit()

def pull():
	for account in accounts:
		getTweets(account)
	
	
def readTweets():
	global currentlyDisplayed
	tweets = []
	for t in db.session.query(Tweet.tweetID).order_by(Tweet.time)[currentlyDisplayed:currentlyDisplayed+5]:
		tweets.append(t[0])
		# print(t[0])
	shuffle(tweets)
	currentlyDisplayed+=5
	return tweets


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=pull,
    trigger=IntervalTrigger(minutes=10),
    id='pullTweets',
    name='Pull Tweets every 10 minutes',
    replace_existing=True)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
def index():
	# pull()
	tweets = readTweets()
	print(tweets)
	return render_template("page.html",tweets=tweets)

@app.route('/update',methods = ["POST"])
def update():
	print("UPDATE CALLED")
	pull()
	tweets = readTweets()
	return jsonify({'data': render_template('update.html', tweets=tweets)})

@app.route('/loadMore',methods = ["POST"])
def loadMore():
	print("LM CALLED")
	tweets = readTweets()
	return jsonify({'data': render_template('update.html', tweets=tweets)})
