from typing import Tuple

from core.ProjectAliceExceptions import SkillStartingFailed
from core.base.model.Intent import Intent
from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import AnyExcept, Online
from core.commons import constants
import discord
import asyncio
import uuid
from paho.mqtt.client import MQTTMessage
import json


class DiscordHook(AliceSkill):
	"""
	Author: philipp2310
	Description: Bring your bot to Discord
	"""

	def __init__(self):
		self.loop = asyncio.get_event_loop()
		self.client = discord.Client(loop=self.loop)
		self.client.event(self.on_message)
		self.client.event(self.on_ready)

		super().__init__()

	def onStart(self):
		super().onStart()
		#TODO get more logic thread names
		self.ThreadManager.newThread(name='otto', target=self.client.run, args={self.getConfig("botToken"),})

	def onStop(self):
		self.ThreadManager.terminateThread(name='otto')
		super().onStop()


	def getChanByName(self, name: str):
		for chan in self.client.get_all_channels():
			if chan.name == name:
				return chan


	def stopDiscord(self):
		return


	#@client.event
	async def on_ready(self):
		self.logInfo('I have logged into Discord as {0.user}'.format(self.client))


	#@client.event
	async def on_message(self, message):
		if message.author == self.client.user:
			return

		if self.client.user.mentioned_in(message):
			async with message.channel.typing():
				#TODO make allowed categorys configurable
				#TODO maybe make only customized channels available as well: prevent Discord user to add channel and hear from new rooms!
				if message.channel.category.name == 'Home':
					try:
						siteId = message.channel.name
						sessionId = str(uuid.uuid4())
						newmessage = MQTTMessage()
						newmessage.payload = json.dumps({'sessionId': sessionId, 'siteId': siteId})
						session = self.DialogSessionManager.addSession(sessionId=sessionId, message=newmessage)
						session.isAPIGenerated = True
						self.MqttManager.publish(topic=constants.TOPIC_NLU_QUERY, payload={ 'input'	: message.content.replace("<@!" + str(self.client.user.id)+">", ""), 'sessionId': session.sessionId })
					except Exception as e:
						self.logError(f'Failed processing: {e}')
				else:
					await message.channel.send("Hier darf ich nicht mit dir reden!")


	# Alice Voice event!
	def onSay(self, session: DialogSession):
		chan = self.getChanByName(session.siteId)
		if chan:
			coro = chan.send(session.payload['text'])
			asyncio.run_coroutine_threadsafe(coro, self.loop)
		else:
			self.logInfo("Not relevant")

