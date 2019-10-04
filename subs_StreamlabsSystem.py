# ---------------------------------------
#   Import Libraries
# ---------------------------------------
import clr
import re
import random
import time
import json
import codecs
import os

clr.AddReference("IronPython.Modules.dll")

# ---------------------------------------
#   [Required]  Script Information
# ---------------------------------------
ScriptName = "Subs"
Website = "https://www.twitch.tv/frittenfettsenpai"
Description = "Sub Event Listener."
Creator = "frittenfettsenpai"
Version = "0.1.0"

reUserNotice = re.compile(r"(?:^(?:@(?P<irctags>[^\ ]*)\ )?:tmi\.twitch\.tv\ USERNOTICE)")

# ---------------------------------------
#   [Required] Intialize Data (Only called on Load)
# ---------------------------------------
def Init():
    global prices, settings
    pricesfile = os.path.join(os.path.dirname(__file__), "prices.json")
    settingsfile = os.path.join(os.path.dirname(__file__), "settings.json")

    try:
        with codecs.open(pricesfile, encoding="utf-8-sig", mode="r") as f:
            prices = json.load(f, encoding="utf-8")
    except:
        prices = []
    try:
        with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
            settings = json.load(f, encoding="utf-8")
    except:
        settings = {
            "blankPriceName": "Trostpreis {0} {1}",
            "blankCurrencyPrice": 500,
            "onSubGiftGiveGifterThePrice": 1,
            "languagePreMessageSubgift": "@{0} gifted ein Sub an @{1}.",
            "languagePreMessageAnonSubgift": "Jemand anonymes gifted ein Sub an @{1}.",
            "languagePreMessageResub": "@{0} danke fuer deinen {1}. Resub <3",
            "languagePreMessageSub": "@{0} danke fuer deinen ersten Sub <3",
            "languageAsThanks": "Als kleinen Dank bekommt @{0}: {1}"
        }
    return


# ---------------------------------------
#   [Required] Execute Data / Process Messages
# ---------------------------------------
def Execute(data):
    global prices
    if data.IsRawData() and data.IsFromTwitch():
        usernotice = reUserNotice.search(data.RawData)
        if usernotice:
            # Parse IRCv3 tags in a dictionary
            tags = dict(re.findall(r"([^=]+)=([^;]*)(?:;|$)", usernotice.group("irctags"))) # https://dev.twitch.tv/docs/irc/tags/

            message = ""
            recipientId = None
            recipientName = None
            priceWon = None

            if tags["msg-id"] == "subgift":
                message = settings["languagePreMessageSubgift"].format(tags["login"], tags["msg-param-recipient-display-name"])
                if settings["onSubGiftGiveGifterThePrice"]:
                    recipientId = tags["user-id"]
                    recipientName = tags["login"]
                else:
                    recipientId = tags["msg-param-recipient-id"]
                    recipientName = tags["msg-param-recipient-display-name"]
            if tags["msg-id"] == "anonsubgift":
                message = settings["languagePreMessageAnonSubgift"].format(tags["msg-param-recipient-display-name"])
                recipientId = tags["msg-param-recipient-id"]
                recipientName = tags["msg-param-recipient-display-name"]
            elif tags["msg-id"] == "resub":
                message = settings["languagePreMessageResub"].format(tags["login"], str(tags["msg-param-cumulative-months"]))
                recipientId = tags["user-id"]
                recipientName = tags["login"]
            elif tags["msg-id"] == "sub":
                message = settings["languagePreMessageSub"].format(tags["login"])
                recipientId = tags["user-id"]
                recipientName = tags["login"]
            else:
                return

            for price in prices:
                random.seed(time.clock())
                randomCount = random.randint(0, 20000)  # streamlabs chatbot is drunk. Max random value has always to be double
                if price['chance'] and randomCount <= price['chance']:
                    priceWon = price["name"]
                    if price["type"] == "currency":
                        if str(price["value"]) == "":
                            price["value"] = 100
                        Parent.AddPoints(recipientId, int(price["value"]))

                    if price["sound"] != "":
                        soundfile = os.path.join(os.path.dirname(__file__), price["sound"])
                        soundVolume = float(price['soundVolume'])
                        if soundVolume == 0 or soundVolume > 1:
                            soundVolume = 1
                        Parent.PlaySound(soundfile, soundVolume)
                    break

            if priceWon is None:
                priceWon = settings["blankPriceName"].format(str(settings["blankCurrencyPrice"]), Parent.GetCurrencyName())
                Parent.AddPoints(recipientId, int(settings["blankCurrencyPrice"]))

            message = message + " " + settings["languageAsThanks"].format(recipientName, priceWon)
            Parent.SendTwitchMessage(message)
    return


# ---------------------------------------
#	[Required] Tick Function
# ---------------------------------------
def Tick():
    return