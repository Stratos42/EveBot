from util import hook, http, timesince
import eveapi
import locale
import time, datetime
import evesurvey

def db_init(db):
    db.execute("create table if not exists EveKey(nick, keyID, vCode, character, primary key(nick, character))")
    db.commit()

def db_corp_init(db):
    db.execute("create table if not exists CorpKey(nick primary key, keyID, vCode, corpname)")
    db.commit()

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

    db.execute("create table if not exists EveKey(nick primary key, keyID, vCode, character)")

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
        res=evesurvey.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evesurvey.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        wallet = auth.char.AccountBalance(characterID=cid)
        isk = wallet.accounts[0].balance
        if isk:
            say("%s has %s ISK." % (charName.title(), locale.format('%.2f', isk, True)))
        else:
            say("No character found.")
    except RuntimeError as e:
        return "Error: ", e.message

@hook.command(autohelp=False)
def eta(inp, nick='', chan='', db=None, say=None, input=None):
    ".eta [Nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evesurvey.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evesurvey.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        skill = auth.char.SkillInTraining(characterID=cid)
        if skill.skillInTraining == 0:
            say("No skill in training")
        else:
            print "Skill in training"
            s=api.eve.TypeName(ids=skill.trainingTypeID)
            skillName=s.types[0].typeName
            t, d=evesurvey.sectostr(time.time(), skill.trainingEndTime)
            msg = "%s: Currently training '%s' to lvl %d (finish in %s, %s)" \
                  % (charName.title(), skillName, skill.trainingToLevel, t, d)
            say(msg)
    except RuntimeError as e:
        return "Error: ", e.message

@hook.command(autohelp=False)
def next(inp, nick='', chan='', db=None, say=None, input=None):
    ".next [Nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evesurvey.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evesurvey.get_characterID(keyID, vCode, charName)
        if cid == None:
            return "No character found"
        queue = auth.char.SkillQueue(characterID=cid).skillqueue
        if len(queue) > 1:
            s=api.eve.TypeName(ids=queue[1].typeID)
            skillName=s.types[0].typeName
            t, d=evesurvey.sectostr(time.time(), queue[1].endTime)
            msg = "%s: Next skill in queue '%s' to lvl %d (finish in %s, %s)" \
                  % (charName.title(), skillName, queue[0].level, t, d)
            say(msg)
        else:
            say("No skill in queue.")
    except RuntimeError as e:
        return "Error: ", e.message

@hook.command(autohelp=False)
def queue(inp, nick='', chan='', db=None, say=None, input=None):
    ".queue [nick]"
    db_init(db)
    if not inp:
        pass
    else:
        nick = inp
    try:
        res=evesurvey.get_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .eveadd"
        keyID, vCode, charName = res
        api, auth, cid=evesurvey.get_characterID(keyID, vCode, charName)
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
        t, d=evesurvey.sectostr(time.time(), qEnd)
        msg = "%s: Skill in queue: %s (finish in %s, %s)" % (charName.title(), snk, t, d)
        say(msg)
    except RuntimeError as e:
        return "Error: ", e.message


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

    db_corp_init(db)

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

    db_corp_init(db)
    db.execute("delete from CorpKey where nick=lower(?)", (nick,))
    db.commit()
    say("Entry %s deleted" % nick)

@hook.command(autohelp=False)
def corp(inp, nick='', chan='', db=None, say=None, input=None):
    ".corp [isk]"
    db_corp_init(db)
    locale.setlocale(locale.LC_ALL, '')
    # if not inp:
    #     return ".corp isk"
    try:
        res=evesurvey.get_corp_apiID_by_nick(db, nick)
        if res == None:
            return "No entry found. Please use .corpadd"
        keyID, vCode, corpName = res
        api, auth, cid=evesurvey.get_characterID(keyID, vCode)
        if cid == None:
            return "No character found"
        wallet = auth.corp.AccountBalance(characterID=cid)
        isk = wallet.accounts[0].balance
        if isk:
            say("%s has %s ISK in Master Wallet." % (corpName.title(), locale.format('%.2f', isk, True)))
        else:
            say("No corporation found.")
    except RuntimeError as e:
        return "Error: ", e.message
