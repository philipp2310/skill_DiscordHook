from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
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
		super().__init__()
		self.loop = asyncio.get_event_loop()
		self.client = discord.Client(loop=self.loop)
		self.client.event(self.on_message)
		self.client.event(self.on_ready)
		self.allowedChans = self.getConfig("allowedSiteIDs").split(",")



	def onStart(self):
		super().onStart()
		self.loop.create_task(self.client.start(self.getConfig("botToken")))
		self.ThreadManager.newThread(name='DiscordHook', target=self.loop.run_forever)

	def onStop(self):
		self.ThreadManager.terminateThread(name='DiscordHook')
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
				if message.channel.name in self.allowedChans:
					try:
						siteId = message.channel.name
						sessionId = str(uuid.uuid4())
						newMessage = MQTTMessage()
						newMessage.payload = json.dumps({'sessionId': sessionId, 'siteId': siteId})
						session = self.DialogSessionManager.addSession(sessionId=sessionId, message=newMessage)
						session.isAPIGenerated = True
						self.MqttManager.publish(topic=constants.TOPIC_NLU_QUERY, payload={ 'input'	: message.content.replace("<@!" + str(self.client.user.id)+">", ""), 'sessionId': session.sessionId })
					except Exception as e:
						self.logError(f'Failed processing: {e}')
				else:
					await message.channel.send(self.randomTalk("chanForbidden"))


	# Alice Voice event!
	def onSay(self, session: DialogSession):
		if session.siteId in self.allowedChans:
			chan = self.getChanByName(session.siteId)
			if chan:
				coro = chan.send(session.payload['text'])
				asyncio.run_coroutine_threadsafe(coro, self.loop)
