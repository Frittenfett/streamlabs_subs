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
import datetime

clr.AddReference("IronPython.Modules.dll")

# ---------------------------------------
#   [Required]  Script Information
# ---------------------------------------
ScriptName = "Subs"
Website = "https://www.twitch.tv/frittenfettsenpai"
Description = "Sub Event Listener & Gachapon."
Creator = "frittenfettsenpai"
Version = "0.9.0"

reUserNotice = re.compile(r"(?:^(?:@(?P<irctags>[^\ ]*)\ )?:tmi\.twitch\.tv\ USERNOTICE)")

# ---------------------------------------
#   [Required] Intialize Data (Only called on Load)
# ---------------------------------------
def Init():
    global prices, settings, jackpot, steamkeys, gachaponprices
    pricesfile = os.path.join(os.path.dirname(__file__), "data_prices.json")
    jackpotfile = os.path.join(os.path.dirname(__file__), "data_jackpot.txt")
    steamkeysfile = os.path.join(os.path.dirname(__file__), "data_steamkeys.json")
    settingsfile = os.path.join(os.path.dirname(__file__), "settings.json")
    gachaponfile = os.path.join(os.path.dirname(__file__), "gachapon.json")

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
            "languageAsThanks": "Als kleinen Dank bekommt @{0}: {1}",
            "languageJackpot": "JACKPOT!!!!111EinsElf @{0} bekommt unglaubliche {1} {2}! Jackpot ist nun wieder leer.",
            "languageKeyError": "You would have won a random steam key.... But this streamer is poor and has no keys lel",
            "languageSteamKeyWhisperPublic": "Der Key wurde dir eben via Twitch gewhispert.",
            "languageSteamKeyWhisper": "Hallo {0}, ich wuensch dir viel Spass mit dem Spiel {1}. Der Code hierfuer ist {2}.",
            "languageJackPotAdded": "{0} {1} wurden in den Jackpot hinzugefuegt. Dieser beinhaltet nun {2} {1}.",
            "enableGachapon": False,
            "gachaponcommand": "!spin",
            "tryCosts": 1000,
            "userCooldown": 600,
            "soundVolume": 1,
            "languageNoMoney": "@{0} you need atleast {1} {2}!",
            "languageCooldown": "@{0} you have to wait {1} seconds to use {2} again!",
            "languageWin": "@{0} wins: {1} (Chance {2}%)",
            "languageNothing": "Nothing",
        }

    try:
        with codecs.open(jackpotfile, encoding="utf-8-sig", mode="r") as f:
            jackpot = int(f.read())
    except:
        jackpot = 0

    try:
        with codecs.open(steamkeysfile, encoding="utf-8-sig", mode="r") as f:
            steamkeys = json.load(f, encoding="utf-8")
    except:
        steamkeys = []

    try:
        with codecs.open(gachaponfile, encoding="utf-8-sig", mode="r") as f:
            gachaponprices = json.load(f, encoding="utf-8")
    except:
        gachaponprices = []

    return


# ---------------------------------------
#   [Required] Execute Data / Process Messages
# ---------------------------------------
def Execute(data):
    global prices, settings, jackpot, gachaponprices

    # ========================================
    # Sub Triggered Events
    # ========================================
    if data.IsRawData() and data.IsFromTwitch():
        usernotice = reUserNotice.search(data.RawData)
        if usernotice:
            # Parse IRCv3 tags in a dictionary
            tags = dict(re.findall(r"([^=]+)=([^;]*)(?:;|$)", usernotice.group("irctags")))  # https://dev.twitch.tv/docs/irc/tags/
            priceWon = None
            jackpotPriceValue = 0

            if tags["msg-id"] == "subgift":
                message = settings["languagePreMessageSubgift"].format(tags["login"], tags["msg-param-recipient-display-name"])
                if settings["onSubGiftGiveGifterThePrice"]:
                    recipientId = tags["login"]
                    recipientName = tags["display-name"]
                else:
                    recipientId = tags["msg-param-recipient-id"]
                    recipientName = tags["msg-param-recipient-display-name"]
            elif tags["msg-id"] == "anonsubgift":
                message = settings["languagePreMessageAnonSubgift"].format(tags["msg-param-recipient-display-name"])
                recipientId = tags["msg-param-recipient-id"]
                recipientName = tags["msg-param-recipient-display-name"]
            elif tags["msg-id"] == "resub":
                message = settings["languagePreMessageResub"].format(tags["login"], str(tags["msg-param-cumulative-months"]))
                recipientId = tags["login"]
                recipientName = tags["display-name"]
            elif tags["msg-id"] == "sub":
                message = settings["languagePreMessageSub"].format(tags["login"])
                recipientId = tags["login"]
                recipientName = tags["display-name"]
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
                    if price["type"] == "currency4all":
                        if str(price["value"]) == "":
                            price["value"] = 100
                        ActiveUsers = Parent.GetActiveUsers()
                        myDict = {}
                        for username in ActiveUsers:
                            myDict[username] = int(price["value"])
                        Parent.AddPointsAll(myDict)
                    elif price["type"] == "vip":
                        Parent.SendTwitchMessage("/vip " + recipientName)
                    elif price["type"] == "steamkey":
                        randomSteamKey = GetRandomSteamKeys()
                        if randomSteamKey == None:
                            errorMessage = settings["languageKeyError"]
                            Parent.SendTwitchMessage(errorMessage)
                            AddPriceToHistory(recipientName, priceWon, errorMessage)
                            return
                        else:
                            priceWon = price["name"] + " :: " + randomSteamKey["game"] + ". " + settings["languageSteamKeyWhisperPublic"]
                            Parent.SendStreamWhisper(recipientId, settings["languageSteamKeyWhisper"].format(recipientName, randomSteamKey["game"], randomSteamKey["key"]))
                    elif price["type"] == "jackpot":
                        Parent.AddPoints(recipientId, int(jackpot))
                        message = settings["languageJackpot"].format(recipientName, str(jackpot), Parent.GetCurrencyName())
                        Parent.SendTwitchMessage(message)
                        SetJackPot(0)
                        AddPriceToHistory(recipientName, priceWon, message)
                        return

                    if price["jackpotValue"] != None and price["jackpotValue"] > 0:
                        jackpotPriceValue = int(price["jackpotValue"])

                    if price["sound"] != None and price["sound"] != "":
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
            if jackpotPriceValue > 0:
                jackpot = jackpot + int(jackpotPriceValue)
                SetJackPot(jackpot)
                message = message + ". " + settings["languageJackPotAdded"].format(str(jackpotPriceValue), Parent.GetCurrencyName(), str(jackpot))
            Parent.SendTwitchMessage(message)
            AddPriceToHistory(recipientName, priceWon, message)

    # ========================================
    # Gachapon System
    # ========================================
    if data.IsChatMessage():
        user = data.User
        username = Parent.GetDisplayName(user)

        if settings["enableGachapon"] and data.GetParam(0).lower() == settings["gachaponcommand"]:
            if Parent.IsOnUserCooldown("Gachapon", settings["gachaponcommand"], user) and Parent.HasPermission(user, "Caster", "") == False:
                cooldown = Parent.GetUserCooldownDuration("Gachapon", settings["gachaponcommand"], user)
                Parent.SendTwitchMessage(settings["languageCooldown"].format(username, cooldown, settings["gachaponcommand"]))
                return

            if Parent.GetPoints(user) < settings['tryCosts']:
                Parent.SendTwitchMessage(settings["languageNoMoney"].format(username, settings['tryCosts'], Parent.GetCurrencyName()))
                return
            Parent.AddUserCooldown(ScriptName, settings['gachaponcommand'], user, settings['userCooldown'])
            Parent.RemovePoints(user, int(settings['tryCosts']))

            priceWon = ""
            for gachaponprice in gachaponprices:
                chance = gachaponprice["chance"]
                random.seed(time.clock())
                randomCount = random.randint(0, 20000) #streamlabs chatbot is drunk. Max random value has always to be double
                if randomCount <= chance:
                    priceWon = gachaponprice["name"]
                    if gachaponprice["type"] == "currency":
                        if str(gachaponprice["value"]) == "":
                            gachaponprice["value"] = 100
                        Parent.AddPoints(user, int(gachaponprice["value"]))
                    if gachaponprice["type"] == "timeout":
                        if str(gachaponprice["value"]) == "":
                            gachaponprice["value"] = 1
                        Parent.SendTwitchMessage("/timeout "+username+" "+str(gachaponprice["value"]))
                    if gachaponprice["type"] == "steamkey":
                       randomSteamKey = GetRandomSteamKeys()
                       if randomSteamKey == None:
                           errorMessage = settings["languageKeyError"]
                           Parent.SendTwitchMessage(errorMessage)
                           AddPriceToHistory(username, priceWon, errorMessage)
                           return
                       else:
                           priceWon = priceWon + " :: " + randomSteamKey["game"] + ". " + settings["languageSteamKeyWhisperPublic"]
                           Parent.SendStreamWhisper(user, settings["languageSteamKeyWhisper"].format(username, randomSteamKey["game"], randomSteamKey["key"]))

                    if gachaponprice["sound"] != "":
                        soundfile = os.path.join(os.path.dirname(__file__), gachaponprice["sound"])
                        Parent.PlaySound(soundfile, settings['soundVolume'])
                    chanceFormated = round(float(gachaponprice["chance"] / 100), 2)
                    Parent.SendTwitchMessage(settings["languageWin"].format(username,str(settings['tryCosts']), Parent.GetCurrencyName(), priceWon, str(chanceFormated)))
                    break

            if priceWon == "":
                Parent.SendTwitchMessage(settings["languageWin"].format(username,str(settings['tryCosts']), Parent.GetCurrencyName(), settings["languageNothing"], "?"))
    return


# ---------------------------------------
#	[Required] Tick Function
# ---------------------------------------
def Tick():
    return


def AddPriceToHistory(receiver, price, message):
    now = datetime.datetime.now()
    datafile = os.path.join(os.path.dirname(__file__), "data_history.txt")
    file = open(datafile, "a")
    file.write(str(now.strftime("%d.%m.%Y %H:%M:%S")) + " " + receiver + " - " + price + " - " + message + " \n")
    file.close()
    return

def GetRandomSteamKeys():
    global steamkeys
    if len(steamkeys) == 0:
        return None

    destiny = random.choice(steamkeys)
    steamkeys.remove(destiny)
    datafile = os.path.join(os.path.dirname(__file__), "data_steamkeys.json")
    try:
        with codecs.open(datafile, encoding="utf-8-sig", mode="w") as f:
            f.write(json.dumps(steamkeys))
            f.close()
            return destiny
    except:
        return None

def SetJackPot(value):
    datafile = os.path.join(os.path.dirname(__file__), "data_jackpot.txt")
    try:
        with codecs.open(datafile, encoding="utf-8-sig", mode="w") as f:
            f.write(str(value))
            f.close()
    except:
        Parent.SendTwitchMessage("Jackpot could not be setted. Ahouh?")