import json
import tweepy
import os


def GetAuth(apiKey, apiSecret, token, tokenSecret):

    # Twitter authentication
    auth = tweepy.OAuthHandler(apiKey, apiSecret)
    auth.set_access_token(
        token, tokenSecret)
    api = tweepy.API(auth)

    try:
        api.verify_credentials()
        return api
    except tweepy.TweepError:
        # Handle authentication error
        print('Failed to authenticate')

    return None

# twitter info
# https://developer.twitter.com/en/apply/user.html
# get twitter id
# http://gettwitterid.com/
