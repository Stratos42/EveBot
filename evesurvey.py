#!/usr/bin/env python

import os
import Queue
import sys
import time
import locale
import time, datetime
import eveapi

def get_apiID_by_nick(db, nick):
    row = db.execute("select keyID, vCode, character from EveKey where nick=?",
                      (nick.lower(),)).fetchall()
    if row:
        return row[0]
    else:
        return None

def get_apiID_by_character(db, char):
    row = db.execute("select nick from EveKey where character=?",
                      (char.lower(),)).fetchall()
    if row:
        return row[0]
    else:
        return None

def get_characterID(keyID, vCode, charName):
    api = eveapi.EVEAPIConnection()
    auth = api.auth(keyID=keyID, vCode=vCode)
    result = auth.account.Characters()
    cid=None
    for char in result.characters:
        if charName == char.name.lower():
            cid=char.characterID
    return api, auth, cid

def sectostr(start, end):
    diff = (end - start)
    sec = datetime.timedelta(seconds=diff)
    d = datetime.datetime(1,1,1) + sec
    print "DEBUG: diff=%d" % diff
    if d.day-1 == 0:
        t =  "%dh %dmn %ds" % (d.hour, d.minute, d.second)
    else:
        t =  "%dd %dh %dmn %ds" % (d.day-1, d.hour, d.minute, d.second)
    d=time.strftime("%A %X %Z", time.localtime(end))
    return t, d

def survey_init(db):
    db.execute("create table if not exists EveSurvey(nick, skill, time, level, character, primary key(nick, character))")
    db.commit()
    row = db.execute("select nick, keyID, vCode, character from EveKey where 1").fetchall()
    for en in row:
        nick, key, code, char = en
        api, auth, cid = get_characterID(key, code, char)
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
            db.execute("insert or replace into EveSurvey(nick, skill, time, level, character) values (?,?,?,?,?)",
                       (nick.lower(), skillName, end, lvl, char.lower()))
            db.commit()

def skill_survey(db):
    row = db.execute("select nick, skill, time, level, character from EveSurvey where 1").fetchall()
    now=time.time()
    for s in row:
        nick, skill, time, level, character = s
