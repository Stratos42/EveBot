EveBot
======

IRC Bot for Eve online (Fork of Skybot: https://github.com/rmmh/skybot)

==Features==
* Multithreaded dispatch and the ability to connect to multiple networks at a time.
* Easy plugin development with automatic reloading and a simple hooking API.
* Plugin for Eve Online (skill training, wallet, market, ...)

==Requirements==
Skybot runs on Python 2.6. Many of the plugins require [[http://codespeak.net/lxml/|lxml]]. It is developed on Ubuntu 9.10 with Python 2.6.4.

==Commands==
Only one character by nick is allowed. 


.eveAdd <KeyID> <vCode> <irc_nick> <Character Name>
	Add an entry for irc_nick in the database
	Key must have rights enabled on SkillInTraining, SkillsQueue, BalanceAccount, MarketOrders
.eveDel
	Delete the entry linked to your nick
.isk [nick]
	Display balance account of your character.
.eta [nick]
	Display the skill in training of your character.
.next [nick]
      Display the next skill in queue.
.queue [nick]
       Display the skills in your skills queue.
.market [nick]
	Display the orders active of your character
.notif init|check
       init: Initialize the DB for notification skill
       check: Debug for admin
.alert start
       Start the notifier daemon.

.corpAdd <KeyID> <vCode> <irc_nick> <Character Name>
	 Add an entry for irc_nick in the database.
	 Key must have rights enabled for the corporation. AccountBalance
.corpDel
	Delete the entry linked to your nick
.corp [isk]
      Display the balance of master wallet

==Todo==
* Improve Notifier daemon (rebuild connection loop)
* Multi character by nick