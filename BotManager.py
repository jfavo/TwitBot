import json, os, tweepy
import TwitterAuth
from random import randint

import time

class BotManager():

    def __init__(self):
        self.bots = []
        self.load_bots()

    def load_bots(self):
        self.check_for_data()

        for dirs in os.listdir('bots/'):
            if os.path.isdir('bots/' + dirs + '/'):
                for file in os.listdir('bots/' + dirs + '/'):
                    if file.endswith('.json'):
                        bot = Bot()
                        bot.load_bot_from_data('bots/' + dirs + '/' + file)
                        self.bots.append(bot)

    
    def check_for_data(self):
        if not os.path.exists('bots'):
            os.makedirs('bots')

    def create_new_bot(self, name, key, keySecret, token, tokenSecret):
        if next((b for b in self.bots if b.nickName == name), None) is not None:
            # A bot already exists with this name
            return False
        elif any(b for b in self.bots if b.apiKey == key) == True:
            # Api key already exists
            return False
        else:
            bot = Bot()
            bot.create_bot(name, key, keySecret, token, tokenSecret)
            bot.save_bot_to_data()
            self.bots.append(bot)
            return True

    def edit_bot(self, prev, name, key, keySecret, token, tokenSecret):

        index = self.bots.index(prev)

        if index is None:
            return "Issues finding previous data"
        elif any(b for b in self.bots if b.nickName.lower() == name.lower()) == True:
            return "Nickname already exists"
        else:

            dirPath = 'bots/' + prev.nickName + '/'
            path = dirPath + prev.nickName
            if os.path.exists(dirPath):
                # Remove previous data
                os.remove(path + '.json')
                os.remove(path + '.log')
                os.rmdir(dirPath)

                # Create new bot to replace the old with the updated one
                bot = Bot()
                bot.create_bot(name, key, keySecret, token, tokenSecret)
                self.bots[index] = bot

                # Save new data
                bot.save_bot_to_data()

            return ""
        

    def delete_bot(self, bot):
        bot = next((b for b in self.bots if b.nickName == bot.nickName), None)

        if bot is not None:
            dirPath = 'bots/' + bot.nickName
            filePath = dirPath + '/' + bot.nickName

            if os.path.exists(filePath + '.json'):
                os.remove(filePath + '.json')
            if os.path.exists(filePath + '.log'):
                os.remove(filePath + '.log')

            if os.path.exists(dirPath):
                os.rmdir(dirPath)
        
            self.bots.remove(bot)


class Bot():

    def __init__(self):
        self.empty = True
        self.running = False
        self.api = None
        self.stream = None

        self.logUpdated = False
        self.updatedLogLines = []
        pass

    def create_bot(self, nickname, apikey, apikeysecret, accesstoken, accesstokensecret):
        self.empty = False
        
        self.nickName = nickname
        self.apiKey = apikey
        self.apiKeySecret = apikeysecret
        self.apiAccessToken = accesstoken
        self.apiAccessTokenSecret = accesstokensecret
        self.targets = []

    def get_api(self):

        try:
            auth = tweepy.OAuthHandler(self.apiKey, self.apiKeySecret)
            auth.set_access_token(self.apiAccessToken, self.apiAccessTokenSecret)
            api = tweepy.API(auth)
        except tweepy.TweepError as e:
            pass
        except:
            print("Issue getting api")

        if api is None or api.verify_credentials() is False:
            return None

        return api

    def turn_on_bot_stream(self):

        if self.running:
            print('Was running')
            return ""

        api = self.get_api()

        if api is None:
            return "There was an issue connecting to Twitter. Check your bots credentials."

        botStreamListener = BotStreamListener(self)
        self.stream = tweepy.Stream(auth = api.auth, listener = botStreamListener)

        following = []
        for target in self.targets:
            following.append(target.user)

        self.stream.filter(follow=following, is_async=True)

        self.update_log("Bot was turned on")

        self.running = True

        return ""

    def turn_off_bot_stream(self):
        
        if self.running:
            self.update_log("Bot was turned off")
            self.stream.disconnect()
            self.running = False

    def load_bot_from_data(self, file):

        try:
            with open(file) as f:
                data = json.load(f)

            self.nickName = data['nickName']
            self.apiKey = data['apiKey']
            self.apiKeySecret = data['apiKeySecret']
            self.apiAccessToken = data['apiAccessToken']
            self.apiAccessTokenSecret = data['apiAccessTokenSecret']
            targets = []
            for t in data['targets']:
                target = BotTarget()
                target.user = t['user']
                target.user_name = t['user_name']
                target.triggers = t['triggers']
                target.replies = t['replies']
                target.replyToAllPosts = t['replyToAllPosts']
                target.favoriteAllPosts = t['favoriteAllPosts']
                targets.append(target)
            self.targets = targets

            self.empty = False

            if not os.path.exists('bots/' + self.nickName + '/' + self.nickName + '.log'):
                open('bots/' + self.nickName + '/' + self.nickName + '.log', 'w')
            
        except:
            print('There was an issue loading the bot for file ' + file)
            self.empty = True


    def save_bot_to_data(self):

        targetData = []
        for target in self.targets:
            targetData.append({
                'user': target.user,
                'user_name': target.user_name,
                'triggers': target.triggers,
                'replies': target.replies,
                'favoriteAllPosts': target.favoriteAllPosts,
                'replyToAllPosts': target.replyToAllPosts
            })

        data = {
            'nickName': self.nickName,
            'apiKey': self.apiKey,
            'apiKeySecret': self.apiKeySecret,
            'apiAccessToken': self.apiAccessToken,
            'apiAccessTokenSecret': self.apiAccessTokenSecret,
            'targets': targetData
        }

        if not os.path.exists('bots/' + self.nickName):
            os.makedirs('bots/' + self.nickName)

        if not os.path.exists('bots/' + self.nickName + '/' + self.nickName + '.log'):
            open('bots/' + self.nickName + '/' + self.nickName + '.log', 'w')

        with open('bots/' + self.nickName + '/' + self.nickName + '.json', 'w') as out:
            json.dump(data, out)

    def get_log(self):
        file = open('bots/' + self.nickName + '/' + self.nickName + '.log', 'r')

        if file:
            return file.read().splitlines()

        return []

    def update_log(self, text):
        path = 'bots/' + self.nickName + '/' + self.nickName + '.log'
        if os.path.exists(path):
            with open(path, 'a') as file:
                rawTime = time.gmtime()
                timestamp = time.strftime("%c", rawTime)

                newLine = timestamp + " - " + text

                if not text.endswith('\n'):
                    file.write('\n')

                file.write(newLine)
                self.updatedLogLines.append(newLine)

                self.logUpdated = True


    def check_if_target_exists(self, id):
        
        for t in self.targets:
            if t.user == id:
                return True

        return False

    def remove_target(self, username):
        target = next((t for t in self.targets if username == t.user_name), None)
        if target is not None:
            self.targets.remove(target)
            self.save_bot_to_data()
            return ""
        else:
            return "There was an issue removing target"


class BotTarget():

    def __init__(self):
        self.user = None
        self.user_name = None
        self.triggers = []
        self.replies = []
        self.favoriteAllPosts = False
        self.replyToAllPosts = False
    
    def set_user(self, id, username):
        self.user = id
        self.user_name = username

    def add_trigger(self, trigger):
        if any(trigger.lower() == t.lower() for t in self.triggers):
            return "Trigger already exists"
        else:
            self.triggers.append(trigger)
            return ""
    
    def add_reply(self, reply):
        if any(reply.lower() == t.lower() for t in self.replies):
            return "Reply already exists"
        else:
            self.replies.append(reply)
            return ""

class BotStreamListener(tweepy.StreamListener):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def on_status(self, status):
        if self.bot.running:
            api = self.bot.get_api()

            if status.user.id == api.me().id:
                # This is triggered by the bot so we will pass over it
                return

            target = next(t for t in self.bot.targets if t.user_name == status.user.screen_name)
            if target is not None:
                if target.favoriteAllPosts:

                    try:
                        api.create_favorite(status.id)
                        self.bot.update_log(f'Favorited tweet "{status.text}" from {status.user.screen_name}')
                    except:
                        print('Failed to favorite tweet')

                if target.replyToAllPosts:
                    tweetId = status.id
                    canReply = True      

                    # Reply to tweet
                    if len(target.replies) > 0:
                        reply = target.replies[randint(0, len(target.replies)-1)]
                    else:
                        canReply = False

                    if len(target.triggers) > 0 and canReply:

                        # Check tweet for one of the trigger words
                        if any(t in status.text.lower().split() for t in target.triggers):   
                            pass
                        else:
                            canReply = False
                    if canReply:
                        try:
                            api.update_status(status = reply, in_reply_to_status_id = status.id, auto_populate_reply_metadata=True)
                            self.bot.update_log(f'Replied to tweet "{status.text}" from {status.user.screen_name} with {reply}')
                        except:
                            self.bot.update_log("There was an issue replying to the tweet")

botManager = BotManager()
