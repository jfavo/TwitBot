
import sys
import tweepy

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QStandardItemModel, QPixmap
from PyQt5.QtWidgets import QWidget, QTabWidget, QListWidget, QListWidgetItem, QHBoxLayout, QApplication, QMainWindow, QGroupBox, QPushButton, QTreeView, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QGridLayout, QMessageBox
import BotManager


class WidgitManager():
    def __init__(self):
        pass

    def show_intro(self, ret = 0):
        self.main = Main()
        self.main.switch_window.connect(self.show_add_creds)
        self.main.switch_window_configure.connect(self.show_bot_configure)
        if ret == 1:
            self.addCreds.close()
        elif ret == 2:
            self.botConfig.close()
        self.main.show()

    def show_add_creds(self, bot):
        self.addCreds = AddCredentials(bot)
        self.addCreds.switch_window.connect(self.show_intro)
        self.main.close()
        self.addCreds.show()
        
    def show_bot_configure(self, bot):
        self.botConfig = BotConfig(bot)
        self.botConfig.switch_window.connect(self.show_intro)
        self.main.close()
        self.botConfig.check_bot_api()
        
        if self.botConfig.api_is_valid is True:
            self.botConfig.init_widget()
            self.botConfig.show()

class Screen(QWidget):

    def __init__(self):
        super().__init__()
        self.moveToOtherScreen = False

    def closeEvent(self, event):
        if self.moveToOtherScreen is True:
            pass
        else:
            choice = QMessageBox.question(self, 'Quitting', 
                                        "Are you sure that you want to quit?",
                                        QMessageBox.Yes | QMessageBox.No)       
            if choice == QMessageBox.Yes:
                self.closeBotStreams()
                pass
            else:
                event.ignore()

    def closeBotStreams(self):
        for bot in BotManager.botManager.bots:
            if bot.stream:
                bot.turn_off_bot_stream()            

class Main(Screen):

    switch_window = pyqtSignal(BotManager.Bot)
    switch_window_configure = pyqtSignal(BotManager.Bot)

    NAME, APIKEY = range(2)

    def __init__(self):
        super().__init__()
        self.logTimers = {}
        self.init_widget()
        
    def init_widget(self):
        self.setWindowTitle('Main')
        self.setGeometry(300, 300, 500, 500)
        self.setFixedSize(500, 500)

        self.btn = QPushButton('Add A Bot', self)
        self.btn.move(250,250)
        self.btn.clicked.connect(lambda: self.go_to_add_creds(None))

        self.dataGroupBox = QGroupBox("Bots")
        self.tabs = QTabWidget()
        self.tabs.resize(450, 200)
        self.add_bots()

        vbox = QVBoxLayout()
        self.dataGroupBox.setLayout(vbox)

        vbox.addWidget(self.tabs)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.dataGroupBox)
        mainLayout.addWidget(self.btn)
        self.setLayout(mainLayout)

    def add_bots(self):
        for bot in BotManager.botManager.bots:
            self.tabs.addTab(self.get_bot_widget(bot), bot.nickName)
            self.logTimers.update({bot.nickName: None})

    def refresh_bot_tabs(self, index):
        self.tabs.removeTab(index)

    def get_bot_widget(self, bot):

        widget = QWidget()
        widget.layout = QVBoxLayout(self)

        # Activity
  
        activityBox = QGroupBox("Activity")

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        nameLabel = QLabel("Bot name: " + bot.nickName)
        statusIcon = QLabel(self)
        self.set_status_icon("pause", statusIcon)

        hbox.addWidget(nameLabel)
        hbox.addStretch(1)
        hbox.addWidget(statusIcon)

        vbox.addLayout(hbox)

        logLayout = QVBoxLayout()
        logLabel = QLabel("Activity Log")

        logList = QListWidget()

        log = bot.get_log()
        if log:
            layer = 0
            for line in log:
                listItem = QListWidgetItem(line)
                logList.insertItem(0, listItem)

        logLayout.addWidget(logLabel)
        logLayout.addWidget(logList)

        vbox.addLayout(logLayout)

        hbox = QHBoxLayout()

        activateBtn = QPushButton("Turn Bot On")
        activateBtn.clicked.connect(lambda: self.activate_btn_click(activateBtn, statusIcon, bot, logList))

        hbox.addStretch(1)
        hbox.addWidget(activateBtn)

        vbox.addLayout(hbox)

        activityBox.setLayout(vbox)
        # Controls

        box = QGroupBox()
        hbox = QHBoxLayout()

        editBtn = QPushButton("Edit Credentials")
        editBtn.clicked.connect(lambda: self.go_to_add_creds(bot))
        configureBtn = QPushButton("Configure Bot")
        configureBtn.clicked.connect(lambda: self.go_to_configure_bot(bot))
        removeBtn = QPushButton("Remove Bot")
        removeBtn.clicked.connect(lambda: self.remove_bot(bot))

        hbox.addWidget(configureBtn)
        hbox.addStretch(1)
        hbox.addWidget(editBtn)
        hbox.addWidget(removeBtn)

        box.setLayout(hbox)

        widget.layout.addWidget(activityBox)
        widget.layout.addStretch(1)
        widget.layout.addWidget(box)

        widget.setLayout(widget.layout)

        return widget

    def remove_bot(self, bot):
        reply = QMessageBox.question(self, 'Confirmation', 
            "Are you sure you want to delete " + bot.nickName, 
            QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            BotManager.botManager.delete_bot(bot)
            self.refresh_bot_tabs(self.tabs.currentIndex())

    def set_status_icon(self, iconType, widget):
        if iconType == "pause":
            pixmap = QPixmap('assets/images/pause-icon.png')
            widget.setToolTip('Bot is not active')
        elif iconType == "running":
            pixmap = QPixmap('assets/images/running-icon.png')
            widget.setToolTip('Bot is active')
        else:
            pixmap = QPixmap('assets/images/error-icon.png')  
            widget.setToolTip('There is an issue!')        

        widget.setPixmap(pixmap)

    def activate_btn_click(self, btn, statusIcon, bot, logList):
        if bot.running:
            # Turn bot off
            bot.turn_off_bot_stream()
            btn.setText("Turn Bot On")
            self.set_status_icon("pause", statusIcon)
        else:
            # Turn bot on
            status = bot.turn_on_bot_stream()
            if status == "":
                if self.logTimers[bot.nickName] is None:
                    self.logTimers[bot.nickName] = QTimer()
                    self.logTimers[bot.nickName].setInterval(1000)
                    self.logTimers[bot.nickName].timeout.connect(lambda: self.update_log_list(bot, logList))
                
                self.logTimers[bot.nickName].start()
                btn.setText("Turn Bot Off")
                self.set_status_icon("running", statusIcon)
            else:
                QMessageBox.warning(self, "Error", status, QMessageBox.Ok)
        pass

    def update_log_list(self, bot, logList):
        for line in bot.updatedLogLines:
            item = QListWidgetItem(line)
            logList.insertItem(0, item)

        bot.updatedLogLines = []

    def go_to_add_creds(self, bot):
        if bot is None:
            bot = BotManager.Bot()
        self.moveToOtherScreen = True
        self.switch_window.emit(bot)

    def go_to_configure_bot(self, bot):
        self.moveToOtherScreen = True
        
        if bot.running:
            bot.turn_off_bot_stream()
            self.logTimers[bot.nickName] = None
        
        self.switch_window_configure.emit(bot)

class AddCredentials(Screen):

    switch_window = pyqtSignal(int)

    def __init__(self, bot):
        super().__init__()

        self.bot = bot

        self.setGeometry(650, 300, 300, 450)
        self.setFixedSize(300, 450)

        self.btn = QPushButton('Back',self)
        self.btn.move(10,10)
        self.btn.clicked.connect(self.go_to_main)

        self.infoBtn = QPushButton('Where Do I Get These?', self)
        self.infoBtn.move(170, 10)
        self.infoBtn.clicked.connect(self.show_info_box)

        self.nameLabel = QLabel(self)
        self.nameLabel.move(20, 80)
        self.nameLabel.setText("Nickname")

        self.apiKeyLabel = QLabel(self)
        self.apiKeyLabel.move(20, 140)
        self.apiKeyLabel.setText("API Key")

        self.apiKeyLabelSecret = QLabel(self)
        self.apiKeyLabelSecret.move(20, 200)
        self.apiKeyLabelSecret.setText("API Key Secret")

        self.accessTokenLabel = QLabel(self)
        self.accessTokenLabel.move(20, 260)
        self.accessTokenLabel.setText("Access Token")

        self.accessTokenSecretLabel = QLabel(self)
        self.accessTokenSecretLabel.move(20, 320)
        self.accessTokenSecretLabel.setText("Access Token Secret")

        self.nameTextBox = QLineEdit(self)
        self.nameTextBox.move(20, 100)
        self.nameTextBox.resize(260, 30)

        self.apiTextBox = QLineEdit(self)
        self.apiTextBox.move(20, 160)
        self.apiTextBox.resize(260, 30)
       
        self.apiSecretTextBox = QLineEdit(self)
        self.apiSecretTextBox.move(20, 220)
        self.apiSecretTextBox.resize(260, 30)
  
        self.tokenTextBox = QLineEdit(self)
        self.tokenTextBox.move(20, 280)
        self.tokenTextBox.resize(260, 30)
  
        self.tokenSecretTextBox = QLineEdit(self)
        self.tokenSecretTextBox.move(20, 340)
        self.tokenSecretTextBox.resize(260, 30)

        if bot.empty is True:
            self.setWindowTitle("Add Credentials")

            self.submitBtn = QPushButton('Add Credentials', self)
        else:
            self.setWindowTitle("Edit Credentials")

            self.nameTextBox.setText(bot.nickName)
            self.apiTextBox.setText(bot.apiKey)
            self.apiSecretTextBox.setText(bot.apiKeySecret)
            self.tokenTextBox.setText(bot.apiAccessToken)
            self.tokenSecretTextBox.setText(bot.apiAccessTokenSecret)

            self.submitBtn = QPushButton('Submit Edits', self)

        self.submitBtn.clicked.connect(self.submit_credentials)
        self.submitBtn.move(200,410)

    def show_info_box(self):
        QMessageBox.question(self, 'Where is this information', 
        "1) You need a twitter account so sign up for one if you do not already have one \n2) Go to this link: https://developer.twitter.com/en/apply/user.html and follow the directions to get to your keys", 
        QMessageBox.Ok)

    def go_to_main(self):
        self.moveToOtherScreen = True
        self.switch_window.emit(1)

    def submit_credentials(self):

        validated = True
        problem = ""

        name = self.nameTextBox.text()
        apiKey = self.apiTextBox.text()
        apiKeySecret = self.apiSecretTextBox.text()
        token = self.tokenTextBox.text()
        tokenSecret = self.tokenSecretTextBox.text()

        if name == "":
            validated = False
            problem = "Please input a Nickname"

        if validated is True and apiKey == "":
            validated = False
            problem = "Please input the api key"

        if validated is True and apiKeySecret == "":
            validated = False
            problem = "Please input the api key secret"

        if validated is True and token == "":
            validated = False
            problem = "Please input the token key"
        
        if validated is True and tokenSecret == "":
            validated = False
            problem = "Please input the token secret key"

        if validated is False:
            QMessageBox.warning(self, 'Issues', 
            problem, 
            QMessageBox.Ok)
        else:
            reply = QMessageBox.question(self, 'Confirmation', 
            "Is this information correct? If these keys are incorrect you will not be able to connect to twitter.", 
            QMessageBox.No, QMessageBox.Yes)

            if reply == QMessageBox.Yes:
                if self.bot.empty is True:
                    if BotManager.botManager.create_new_bot(name, apiKey, apiKeySecret, token, tokenSecret) is True:
                        self.go_to_main()
                else:
                    message = BotManager.botManager.edit_bot(self.bot, name, apiKey, apiKeySecret, token, tokenSecret)
                    if message == "":
                        self.go_to_main()
                    else:
                        QMessageBox.warning(self, 'Issue', message, QMessageBox.Ok)
         
class BotConfig(Screen):

    switch_window = pyqtSignal(int)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.api = self.bot.get_api()
        self.api_is_valid = False

    def init_widget(self):
        self.setWindowTitle('Configure ' + self.bot.nickName)
        self.setFixedSize(550, 700)

        mainLayout = QVBoxLayout()

        # Heading
        hBox = QHBoxLayout()

        self.nameLabel = QLabel("Bot name: " + self.bot.nickName)
        self.statusIcon = QLabel(self)
        self.set_status_icon("pause")

        hBox.addWidget(self.nameLabel)
        hBox.addWidget(self.statusIcon)
        hBox.addStretch()
        vBox = QVBoxLayout()

        vBox.addLayout(hBox)

        mainLayout.addLayout(vBox)

        # Targets

        groupBox = QGroupBox("Target")

        vBox = QVBoxLayout()
        targetsLabel = QLabel("Active Targets: ")

        self.targets = QListWidget()

        hBox = QHBoxLayout()

        removeBtn = QPushButton("Remove Target")
        removeBtn.clicked.connect(self.remove_target)

        hBox.addStretch(1)
        hBox.addWidget(removeBtn)

        vBox.addWidget(targetsLabel)
        vBox.addWidget(self.targets)
        vBox.addLayout(hBox)

        hBox = QHBoxLayout()

        addLabel = QLabel("Add Target By ID")
        infoBtn = QPushButton("Where do I get an ID?")
        infoBtn.clicked.connect(self.get_user_id_info)

        hBox.addWidget(addLabel)
        hBox.addStretch(1)
        hBox.addWidget(infoBtn)

        vBox.addLayout(hBox)

        self.addTargetInput = QLineEdit()

        hBox = QHBoxLayout()

        addUserBtn = QPushButton("Add Target ID")
        addUserBtn.clicked.connect(self.add_target)

        hBox.addStretch(1)
        hBox.addWidget(addUserBtn)

        vBox.addWidget(self.addTargetInput)
        vBox.addLayout(hBox)

        groupBox.setLayout(vBox)

        mainLayout.addWidget(groupBox)

        # Target data

        groupBox = QGroupBox("Target Configuration")
        vBox = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.resize(450, 200)

        self.update_bot_data()

        vBox.addWidget(self.tabs)
        groupBox.setLayout(vBox)

        mainLayout.addWidget(groupBox)

        # Back

        backBtn = QPushButton("Back", self)
        backBtn.clicked.connect(self.go_to_main)

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(backBtn)

        vBox = QVBoxLayout()
        vBox.addLayout(controlsLayout)

        mainLayout.addLayout(vBox)

        self.setLayout(mainLayout)

    def check_bot_api(self):

        if self.api is None:
            QMessageBox.warning(self, 'Error', "We couldn't get access to twitter with the credentials applied to this bot. Double check if your credentials are accurate and try again.", QMessageBox.Ok)
            self.go_to_main()
        else:
            self.api_is_valid = True

    def update_bot_data(self):
        for target in self.bot.targets:
            listItem = QListWidgetItem(target.user_name, self.targets)
            self.tabs.addTab(self.add_tab_widget(target), target.user_name)

    def add_tab_widget(self, target):

        widget = QWidget()

        mainLayout = QVBoxLayout()

        # Reply To All Posts

        hBox = QHBoxLayout()

        replyLabel = QLabel("Reply To All Tweets: ")
        replyLabelSetting = QLabel(str(target.replyToAllPosts))

        replyToggleBtn = QPushButton("Toggle")
        replyToggleBtn.clicked.connect(lambda: self.toggle_target_reply(target, replyLabelSetting))

        hBox.addWidget(replyLabel)
        hBox.addWidget(replyLabelSetting)
        hBox.addStretch(1)
        hBox.addWidget(replyToggleBtn)

        mainLayout.addLayout(hBox)

        # Favorite All Posts

        hBox = QHBoxLayout()

        favoriteLabel = QLabel("Favorite All Tweets: ")
        favoriteLabelSetting = QLabel(str(target.favoriteAllPosts))

        favoriteToggleBtn = QPushButton("Toggle")
        favoriteToggleBtn.clicked.connect(lambda: self.toggle_target_favorites(target, favoriteLabelSetting))

        hBox.addWidget(favoriteLabel)
        hBox.addWidget(favoriteLabelSetting)
        hBox.addStretch(1)
        hBox.addWidget(favoriteToggleBtn)

        mainLayout.addLayout(hBox)

        hBox = QHBoxLayout()

        # Triggers

        groupBox = QGroupBox("Triggers")

        vBox = QVBoxLayout()

        triggerList = QListWidget()

        # Add triggers to list
        for t in target.triggers:
            listItem = QListWidgetItem(t, triggerList)

        btnHBox = QHBoxLayout()

        infoBtn = QPushButton("What Are Triggers?")
        infoBtn.clicked.connect(lambda: self.show_info(1))

        removeBtn = QPushButton("Remove Trigger")
        removeBtn.clicked.connect(lambda: self.remove_trigger(target, triggerList, 1))

        vBox.addWidget(triggerList)

        btnHBox.addWidget(infoBtn)
        btnHBox.addWidget(removeBtn)

        vBox.addLayout(btnHBox)

        addTriggerLabel = QLabel("Add Trigger")
        triggerInput = QLineEdit()

        addTriggerHBox = QHBoxLayout()

        triggerAddBtn = QPushButton("Add")
        triggerAddBtn.clicked.connect(lambda: self.add_trigger(triggerInput, triggerList))

        addTriggerHBox.addStretch(1)
        addTriggerHBox.addWidget(triggerAddBtn)

        vBox.addWidget(addTriggerLabel)
        vBox.addWidget(triggerInput)
        vBox.addLayout(addTriggerHBox)

        groupBox.setLayout(vBox)

        hBox.addWidget(groupBox)

        # Reply Phrases

        groupBox = QGroupBox("Reply Phrases")

        vBox = QVBoxLayout()

        replyList = QListWidget()

        # Add replies to list
        for t in target.replies:
            listItem = QListWidgetItem(t, replyList)
        
        btnHBox = QHBoxLayout()

        infoBtn = QPushButton("What Are Phrases?")
        infoBtn.clicked.connect(lambda: self.show_info(2))

        removeBtn = QPushButton("Remove Phrase")
        removeBtn.clicked.connect(lambda: self.remove_trigger(target, replyList, 2))

        vBox.addWidget(replyList)

        btnHBox.addWidget(infoBtn)
        btnHBox.addWidget(removeBtn)

        vBox.addLayout(btnHBox)

        addPhraseLabel = QLabel("Add Reply")
        phraseInput = QLineEdit()

        addPhraseHBox = QHBoxLayout()

        phraseAddBtn = QPushButton("Add")
        phraseAddBtn.clicked.connect(lambda: self.add_reply(phraseInput, replyList))

        addPhraseHBox.addStretch(1)
        addPhraseHBox.addWidget(phraseAddBtn)

        vBox.addWidget(addPhraseLabel)
        vBox.addWidget(phraseInput)
        vBox.addLayout(addPhraseHBox)

        groupBox.setLayout(vBox)

        hBox.addWidget(groupBox)

        mainLayout.addLayout(hBox)

        widget.setLayout(mainLayout)

        return widget

    def toggle_target_reply(self, target, widget):
        target.replyToAllPosts = not target.replyToAllPosts
        widget.setText(str(target.replyToAllPosts))

    def toggle_target_favorites(self, target, widget):
        target.favoriteAllPosts = not target.favoriteAllPosts
        widget.setText(str(target.favoriteAllPosts))

    def show_info(self, code):
        if code == 1:
            title = "Triggers"
            message = "Triggers are words that the bot will look for. If a trigger is spotted in a tweet by a target, it will reply with one of the phrases."
        else:
            title = "Phrases"
            message = "Phrases are what will be used when responding to the targets tweets."

        QMessageBox.question(self, title, message, QMessageBox.Ok)

    def remove_trigger(self, target, listWidget, code):
        item = listWidget.currentItem()

        if item is not None:
            reply = QMessageBox.question(self, 'Are you sure?', "Are you sure you want to remove " + item.text(), QMessageBox.No | QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                if code == 1:
                    target.triggers.remove(item.text())
                else:
                    target.replies.remove(item.text())
                listWidget.takeItem(listWidget.currentRow())

    def add_trigger(self, lineEdit, listWidget):
        text = lineEdit.text()

        if text == "":
            QMessageBox.warning(self, 'Issue', "Please input a trigger", QMessageBox.Ok)
        else:
            response = self.bot.targets[self.tabs.currentIndex()].add_trigger(text)
            if response != "":
                QMessageBox.warning(self, 'Issue', "Trigger already exists", QMessageBox.Ok)
            else:
                QListWidgetItem(text, listWidget)
                lineEdit.clear()

    def add_reply(self, lineEdit, listWidget):
        text = lineEdit.text()

        if text == "":
            QMessageBox.warning(self, 'Issue', "Please input a phrase", QMessageBox.Ok)
        else:
            response = self.bot.targets[self.tabs.currentIndex()].add_reply(text)
            if response != "":
                QMessageBox.warning(self, 'Issue', "Reply already exists", QMessageBox.Ok)
            else:
                QListWidgetItem(text, listWidget)
                lineEdit.clear()

    def set_status_icon(self, iconType):
        if iconType == "pause":
            pixmap = QPixmap('assets/images/pause-icon.png')
            self.statusIcon.setToolTip('Bot is not active')
        elif iconType == "running":
            pixmap = QPixmap('assets/images/running-icon.png')
            self.statusIcon.setToolTip('Bot is active')
        else:
            pixmap = QPixmap('assets/images/error-icon.png')  
            self.statusIcon.setToolTip('There is an issue!')        

        self.statusIcon.setPixmap(pixmap.scaled(32, 32))

    def remove_target(self):
        target = self.targets.currentItem()

        if target is not None:
            reply = QMessageBox.question(self, 'Are you sure?', "Are you sure you want to remove " + target.text(), QMessageBox.No | QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                if self.bot.remove_target(target.text()) == "":
                    self.tabs.removeTab(self.targets.currentRow())
                    self.targets.takeItem(self.targets.currentRow())
                    

    def get_user_id_info(self):
        QMessageBox.question(self, 'How to get User Id', "Go to http://gettwitterid.com/ and input the twitter user that you wish to target. This will give you their twitter ID", QMessageBox.Ok)

    def add_target(self):
        value = self.addTargetInput.text()
        valid = True
        problem = ""

        if value == "":
            valid = False
            problem = "Please input a target"

        if valid is True:
            if self.bot.check_if_target_exists(value) is False:
                try:
                    user = self.api.get_user(value)

                    if user is not None:
                        target = BotManager.BotTarget()
                        target.user = value
                        target.user_name = user.screen_name
                        self.bot.targets.append(target)
                        self.bot.save_bot_to_data()
                        self.targets.addItem(target.user_name)
                        self.tabs.addTab(self.add_tab_widget(target), target.user_name)

                        self.addTargetInput.setText('')
                    else:
                        QMessageBox.warning(self, 'Issues', 
                            "Twitter doesn't recognize user id", 
                            QMessageBox.Ok)
                except:
                    QMessageBox.warning(self, 'Issues', 
                        "User doesn't exist", 
                        QMessageBox.Ok)
            else:
                QMessageBox.warning(self, 'Issues', 
                    "Target already exists", 
                    QMessageBox.Ok)
        else:
            QMessageBox.warning(self, 'Issues', 
                problem, 
                QMessageBox.Ok)

    def go_to_main(self):
        self.moveToOtherScreen = True
        self.switch_window.emit(2)

    def closeEvent(self, event):
        self.bot.save_bot_to_data()
        super().closeEvent(event)