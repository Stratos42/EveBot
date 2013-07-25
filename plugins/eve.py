from util import hook, http, timesince
import eveapi
import locale
import time, datetime, ssl
import evemisc

def db_init(db):
    db.execute("create table if not exists EveKey(nick primary key, keyID, vCode, character)")
    db.commit()
    db.execute("create table if not exists CorpKey(nick primary key, keyID, vCode, corpname)")
    db.commit()
    db.execute("create table if not exists EveSurvey(nick primary key, skill, time, level, character, bool)")
    db.commit()

global alive

########
######## Character
########

@hook.command
def eveAdd(inp, nick='', chan='', db=None, input=None):
    ".eveAdd <KeyID> <vCode> <irc_nick> <Character Name>"

    datas = inp.split()

    if len(datas) < 3:
        return """Arguments missing:
        Usage: .eveAdd <KeyID> <vCode> <irc_nick> <Character Name>"""

    db_init(db)
    key=datas[0]
    vcode=datas[1]
    nick=datas[2]
    char=' '.join(datas[3:])

    api = eveapi.EVEAPIConnection()
    auth = api.auth(keyID=key, vCode=vcode)

    characters = auth.account.Characters()

    for character in characters.characters:
        print character.name
        if character.name == char:
            db.execute("insert or replace into EveKey(nick, keyID, vCode, character) values (?,?,?,?)",
                       (nick.lower(), key, vcode, char.lower()))
            db.commit()
            return 'Character %s added to database and linked to %s' % (char, nick)
    if not characters:
        return 'No character found'
    return "WTF ?!"

@hook.command(autohelp=False)
def eveDel(inp, nick='', chan='', db=None, say=None, input=None):
    ".eveDel"

    db_init(db)
    db.execute("delete from EveKey where nick=lower(?)", (nick,))
    db.commit()
    say("%s's Character entry deleted" % nick)

@hook.command(autohelp=False)
def isk(inp, nick='', chan='', db=None, say=None, input=None):
    ".isk [Nick]"
    db_init(db)
    locale.setlocale(locale.LC_ALL, '')
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evemisc.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evemisc.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        wallet = auth.char.AccountBalance(characterID=cid)
        isk = wallet.accounts[0].balance
        if isk:
            say("%s has %s ISK." % (charName.title(), locale.format('%.2f', isk, True)))
        else:
            say("No character found.")
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message

@hook.command(autohelp=False)
def eta(inp, nick='', chan='', db=None, say=None, input=None):
    ".eta [Nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evemisc.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evemisc.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        skill = auth.char.SkillInTraining(characterID=cid)
        if skill.skillInTraining == 0:
            say("No skill in training")
        else:
            print "Skill in training"
            s=api.eve.TypeName(ids=skill.trainingTypeID)
            skillName=s.types[0].typeName
            t, d=evemisc.sectostr(time.time(), skill.trainingEndTime)
            msg = "%s: Currently training '%s' to lvl %d (finish in %s, %s)" \
                  % (charName.title(), skillName, skill.trainingToLevel, t, d)
            say(msg)
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message

@hook.command(autohelp=False)
def next(inp, nick='', chan='', db=None, say=None, input=None):
    ".next [Nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evemisc.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evemisc.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        queue = auth.char.SkillQueue(characterID=cid).skillqueue
        if len(queue) > 1:
            s=api.eve.TypeName(ids=queue[1].typeID)
            skillName=s.types[0].typeName
            t, d=evemisc.sectostr(time.time(), queue[1].endTime)
            msg = "%s: Next skill in queue '%s' to lvl %d (finish in %s, %s)" \
                  % (charName.title(), skillName, queue[0].level, t, d)
            say(msg)
        else:
            say("No skill in queue.")
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message

@hook.command(autohelp=False)
def queue(inp, nick='', chan='', db=None, say=None, input=None):
    ".queue [nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evemisc.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evemisc.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        queue = auth.char.SkillQueue(characterID=cid).skillqueue
        snk=""
        qEnd=0
        if len(queue) > 0:
            for sk in queue:
                s=api.eve.TypeName(ids=sk.typeID)
                skillName=s.types[0].typeName
                snk = snk + "[" + skillName + " lvl. " + str(sk.level) + "] "
                qEnd = sk.endTime
        else:
            return "No skill in queue."
        print snk
        t, d=evemisc.sectostr(time.time(), qEnd)
        msg = "%s: Skill in queue: %s (finish in %s, %s)" % (charName.title(), snk, t, d)
        say(msg)
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message

@hook.command(autohelp=False)
def market(inp, nick='', chan='', db=None, say=None, input=None):
    ".market [Nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evemisc.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evemisc.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        orders = auth.char.MarketOrders(characterID=cid).orders
        if not orders:
            say("No market orders in training")
        else:
            msg=""
            for order in orders:
                if order.orderState == 0:
                    name=evemisc.get_name_from_id(api, order.typeID)
                    price=order.price
                    startVol=order.volEntered
                    currentVol=order.volRemaining
                    # t, d=evemisc.sectostr(time.time(), skill.trainingEndTime)
                    if order.bid == 1:
                        msg = "[Buy %d unit of %s for %.2f ISK] %s" % (startVol, name, price, msg)
                    else:
                        msg = "[Sell %d/%d unit of %s for %.2f ISK] %s" % (currentVol, startVol, name, price, msg)
            say(msg)
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message

def update_skill(en, db, create=False):
    nick, key, code, char = en
    api, auth, cid = evemisc.get_characterID(key, code, char)
    skill = auth.char.SkillInTraining(characterID=cid)
    if cid == None:
        return 1
    skill = auth.char.SkillInTraining(characterID=cid)
    if skill.skillInTraining == 0:
        pass
    else:
        s=api.eve.TypeName(ids=skill.trainingTypeID)
        skillName=s.types[0].typeName
        end=skill.trainingEndTime
        lvl=skill.trainingToLevel
        if create == True:
            print "create %s - %s" % (nick, char)
            db.execute("insert into EveSurvey(nick, skill, time, level, character, bool) values (?,?,?,?,?,0)",
                       (nick.lower(), skillName, end, lvl, char.lower()))
        else:
            row = db.execute("select skill, level from EveSurvey where nick=?", (nick.lower(),)).fetchall()
            sn, ls = row[0]
            if skillName == sn and ls == lvl:
                db.execute("update EveSurvey set skill=?, time=?, level=?, character=?, bool=1 where nick=lower(?)",
                           (skillName, end, lvl, char.lower(), nick))
            else:
                db.execute("update EveSurvey set skill=?, time=?, level=?, character=?, bool=0 where nick=lower(?)",
                           (skillName, end, lvl, char.lower(), nick))
        db.commit()
    return nick, char

@hook.command(autohelp=False)
def notif(inp, nick='', chan='', db=None, say=None, input=None):
    db_init(db)
    try:
        if inp == "check":
            now = time.time()
            row = db.execute("select nick, skill, time, level, character from EveSurvey where 1").fetchall()
            for en in row:
                n, skill, end, level, character=en
                print("Next alert for %s: %s (finish in %s)" % (n, skill, evemisc.sectostr(now, end)))
            say("Check OK")
        if inp == "init":
            db.execute("drop table if exists EveSurvey")
            db.commit()
            row = db.execute("select nick, keyID, vCode, character from EveKey where 1").fetchall()
            for en in row:
                n, c =update_skill(en, db, True)
            say("DB Updated")
        if inp == "stop":
            global alive
            alive = False
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message


@hook.singlethread
@hook.command(autohelp=False)
def alert(inp, nick='', chan='', db=None, say=None, input=None):
    db_init(db)
    try:
        if inp == "start":
            say("Start skill notifier")
            global alive
            alive = True
            while alive:
                now = time.time()
                row = db.execute("select nick, skill, time, level, character, bool from EveSurvey where 1").fetchall()
                for en in row:
                    n, skill, end, level, character, boo=en
                    if end <= now:
                        t, d=evemisc.sectostr(end, now)
                        msg = "%s: Your character %s has finished to train '%s' to lvl %d (since %s)" % (n.title(), character.title(), skill, level, t)
                        if boo == 0:
                            say(msg)
                        msg=None
                        row = db.execute("select nick, keyID, vCode, character from EveKey where nick=lower(?)", (n,)).fetchall()
                        update_skill(row[0], db)
                        break
                time.sleep(5)
                print ("Notifier is alive")
            say("Stopping skill notifier...")
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message


#########
######### Corporation
#########

@hook.command
def corpAdd(inp, nick='', chan='', db=None, input=None):
    ".corpAdd <KeyID> <vCode> <irc_nick> <Character Name>"

    datas = inp.split()

    if len(datas) < 3:
        return """Arguments missing:
        Usage: .corpAdd <KeyID> <vCode> <irc_nick> <Corporation Name>"""

    db_init(db)

    key=datas[0]
    vcode=datas[1]
    nick=datas[2]
    corp=' '.join(datas[3:])

    api = eveapi.EVEAPIConnection()
    auth = api.auth(keyID=key, vCode=vcode)

    characters = auth.account.Characters()
    if not characters:
        return 'No character found'
    db.execute("insert or replace into CorpKey(nick, keyID, vCode, corpname) values (?,?,?,?)",
               (nick.lower(), key, vcode, corp.lower()))
    db.commit()
    return 'Corporation %s added to database and linked to %s' % (corp.title(), nick)

@hook.command(autohelp=False)
def corpDel(inp, nick='', chan='', db=None, say=None, input=None):
    ".corpDel"

    db_init(db)
    db.execute("delete from CorpKey where nick=lower(?)", (nick,))
    db.commit()
    say("Entry %s deleted" % nick)

@hook.command(autohelp=False)
def corp(inp, nick='', chan='', db=None, say=None, input=None):
    ".corp [isk]"
    db_init(db)
    locale.setlocale(locale.LC_ALL, '')
    # if not inp:
    #     return ".corp isk"
    try:
        res=evemisc.get_corp_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .corpadd"
        keyID, vCode, corpName = res
        api, auth, cid=evemisc.get_characterID(keyID, vCode)
        if cid == None:
            return "No character found"
        wallet = auth.corp.AccountBalance(characterID=cid)
        isk = wallet.accounts[0].balance
        if isk:
            say("%s has %s ISK in Master Wallet." % (corpName.title(), locale.format('%.2f', isk, True)))
        else:
            say("No corporation found.")
    except (RuntimeError, ssl.SSLError) as e:
        return "Error: " + e.message
