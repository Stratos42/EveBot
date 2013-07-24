from util import hook, http, timesince
import eveapi
import locale
import time, datetime
import evesurvey

def db_init(db):
    db.execute("create table if not exists EveKey(nick, keyID, vCode, character, primary key(nick, character))")
    db.commit()

@hook.command
def eveAdd(inp, nick='', chan='', db=None, input=None):
    ".keyAdd <KeyID> <vCode> <irc_nick> <Character Name>"

    datas = inp.split()

    if len(datas) < 4:
        return """Arguments missing:
        Usage: .keyAdd <KeyID> <vCode> <irc_nick> <Character Name>"""

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

@hook.command
def eveDel(inp, nick='', chan='', db=None, say=None, input=None):
    ".keyDel <Character Name>"

    db_init(db)

    res=evesurvey.get_apiID_by_character(db, inp)
    if res == None:
        say("No entry for %s" % inp)

    if res[0] == nick.lower():
        db.execute("delete from EveKey where nick=lower(?) and character=lower(?)", (nick, inp))
        db.commit()
        say("Entry %s deleted" % inp)
    return "Nothing to delete"

@hook.command(autohelp=False)
def isk(inp, nick='', chan='', db=None, say=None, input=None):
    ".isk [Character Name]"
    db_init(db)
    locale.setlocale(locale.LC_ALL, '')
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
    ".eta"
    db_init(db)
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
    ".next"
    db_init(db)
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
    ".queue"
    db_init(db)
    if nick.lower() == "captain_fake":
        return "Queue not found."
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
        msg = "%s: Skill in queue: %s (finish in %s)" % (charName.title(), snk, t)
        say(msg)
    except RuntimeError as e:
        return "Error: ", e.message

