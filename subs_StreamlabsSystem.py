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
Version = "1.0.0"

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
            "onSubGiftGiveGifterThePrice": 1,
            "languagePreMessageSubgift": "@{0} gifted ein Sub an @{1}.",
            "languagePreMessageAnonSubgift": "Jemand anonymes gifted ein Sub an @{1}.",
            "languagePreMessageResub": "@{0} danke fuer deinen {1}. Resub <3",
            "languagePreMessageSub": "@{0} danke fuer deinen ersten Sub <3",
            "languageAsThanks": "Als kleinen Dank bekommt @{0}: {1} (Chance {2}%)",
            "languagePrice": "{0} (Chance {1}%)",
            "languageJackpot": "JACKPOT!!!!111EinsElf @{0} bekommt unglaubliche {1} {2}! Jackpot ist nun wieder leer.",
            "languageKeyError": "You would have won a random steam key.... But this streamer is poor and has no keys lel",
            "languageSteamKeyWhisperPublic": "Der Key wurde dir eben via Twitch gewhispert.",
            "languageSteamKeyWhisper": "Hallo {0}, ich wuensch dir viel Spass mit dem Spiel {1}. Der Code hierfuer ist {2}.",
            "languageJackPotAdded": "{0} {1} wurden in den Jackpot hinzugefuegt. Dieser beinhaltet nun {2} {1}.",
            "enableGachapon": False,
            "enableSub": False,
            "gachaponcommand": "!spin",
            "tryCosts": 1000,
            "userCooldown": 600,
            "soundVolume": 1,
            "languageNoMoney": "@{0} you need atleast {1} {2}!",
            "languageCooldown": "@{0} you have to wait {1} seconds to use {2} again!",
            "languageWin": "@{0} uses {1} {2} and wins:",
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
    if data.IsRawData() and data.IsFromTwitch() and settings["enableSub"]:
        usernotice = reUserNotice.search(data.RawData)
        if usernotice:
            # Parse IRCv3 tags in a dictionary
            tags = dict(re.findall(r"([^=]+)=([^;]*)(?:;|$)", usernotice.group("irctags")))  # https://dev.twitch.tv/docs/irc/tags/

            responsefile = os.path.join(os.path.dirname(__file__), "response.txt")
            file = open(responsefile, "a")
            file.write(str(tags) + "\n" + str(usernotice) + " \n\n\n")
            file.close()

            if tags["msg-id"] == "subgift":
                message = settings["languagePreMessageSubgift"].format(tags["login"], tags["msg-param-recipient-display-name"])
                if tags['login'] == "ananonymousgifter":
                    recipientId = tags["msg-param-recipient-id"]
                    recipientName = tags["msg-param-recipient-display-name"]
                elif settings["onSubGiftGiveGifterThePrice"]:
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

            CalculateAndSubmitPrice("sub", message, recipientId, recipientName, prices)

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

            message = settings["languageWin"].format(username, str(settings['tryCosts']), Parent.GetCurrencyName())
            CalculateAndSubmitPrice("gachapon", message, user, username, gachaponprices)
    return


# ---------------------------------------
#	[Required] Tick Function
# ---------------------------------------
def Tick():
    return


def AddPriceToHistory(type, receiver, price, message):
    now = datetime.datetime.now()
    datafile = os.path.join(os.path.dirname(__file__), "data_history.txt")
    file = open(datafile, "a")
    file.write(str(now.strftime("%d.%m.%Y %H:%M:%S")) + " " + type + " " + receiver + " - " + price + " - " + message + " \n")
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


def CalculateAndSubmitPrice(type, message, user, username, priceList):
    global settings, jackpot

    random.shuffle(priceList)
    #Build up price matrix
    priceMatrix = []
    matrixKey = 0
    chanceMaximum = 0
    for price in priceList:
        chanceMaximum += price["chance"]
        limit = matrixKey + price["chance"]
        while matrixKey < limit:
            priceMatrix.append(price)
            matrixKey += 1

    #Get price
    random.seed(time.clock())
    priceWon = random.choice(priceMatrix)


    chanceFormated = round(float(priceWon["chance"] / float(chanceMaximum) * 100), 2)

    #Submit price
    SubmitPrice(type, message, user, username, priceWon, chanceFormated)
    return


def SubmitPrice(type, message, user, username, priceWon, chanceFormated):
    global settings, jackpot

    if priceWon["type"] == "currency":
        if str(priceWon["value"]) == "":
            priceWon["value"] = 100
        Parent.AddPoints(user, int(priceWon["value"]))
    elif priceWon["type"] == "timeout":
        if str(priceWon["value"]) == "":
            priceWon["value"] = 1
        Parent.SendTwitchMessage("/timeout " + username + " " + str(priceWon["value"]))
    elif priceWon["type"] == "steamkey":
        randomSteamKey = GetRandomSteamKeys()
        if randomSteamKey == None:
            errorMessage = settings["languageKeyError"]
            Parent.SendTwitchMessage(errorMessage)
            AddPriceToHistory(type, username, priceWon, errorMessage)
            return
        else:
            priceWon = priceWon + " :: " + randomSteamKey["game"] + ". " + settings["languageSteamKeyWhisperPublic"]
            Parent.SendStreamWhisper(user, settings["languageSteamKeyWhisper"].format(username, randomSteamKey["game"],randomSteamKey["key"]))
    elif priceWon["type"] == "currency4all":
        if str(priceWon["value"]) == "":
            priceWon["value"] = 100
        ActiveUsers = Parent.GetActiveUsers()
        myDict = {}
        for activeUserName in ActiveUsers:
            myDict[activeUserName] = int(priceWon["value"])
        Parent.AddPointsAll(myDict)
    elif priceWon["type"] == "vip":
        Parent.SendTwitchMessage("/vip " + username)
    elif priceWon["type"] == "jackpot":
        Parent.AddPoints(user, int(jackpot))
        message = message + settings["languageJackpot"].format(username, str(jackpot), Parent.GetCurrencyName())
        Parent.SendTwitchMessage(message)
        SetJackPot(0)
        AddPriceToHistory(type, username, priceWon, message)
        return

    jackpotPriceValue = 0
    if "jackpotAmount" in priceWon and priceWon["jackpotAmount"] > 0:
        jackpotPriceValue = int(priceWon["jackpotAmount"])

    if "sound" in priceWon and priceWon["sound"] != "":
        soundfile = os.path.join(os.path.dirname(__file__), priceWon["sound"])
        soundVolume = float(priceWon['soundVolume'])
        if soundVolume == 0 or soundVolume > 1:
            soundVolume = 1
        Parent.PlaySound(soundfile, soundVolume)

    if type == "sub":
        message = message + " " + settings["languageAsThanks"].format(username, priceWon["name"], chanceFormated)
    else:
        message = message + " " + settings["languagePrice"].format(priceWon["name"], chanceFormated)
    if jackpotPriceValue > 0:
        jackpot = jackpot + int(jackpotPriceValue)
        SetJackPot(jackpot)
        message = message + ". " + settings["languageJackPotAdded"].format(str(jackpotPriceValue), Parent.GetCurrencyName(), str(jackpot))
    Parent.SendTwitchMessage(message)
    return