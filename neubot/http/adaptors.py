# neubot/http/adaptors.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.

import collections
import errno

import neubot

MAXLENGTH = (1<<23)
PIECE = (1<<20)

READING_LENGTH = 0
READING_CHUNK = 1
READING_END = 2
READING_TRAILERS = 3

class adaptor:
	def __init__(self, connection):
		self.connection = connection
		self.connection.set_readable()		# Yep, always
		self.connection.attach(self)
		self.protocol = None
		self.recvbuff = neubot.network.recvbuff()
		self.sendbuff = neubot.network.sendbuff()
		self.sendqueue = collections.deque()
		self.parsers = collections.deque()
		self.chunkstate = -1
		self.chunklength = 0
		self.bodylength = 0

	def closing(self):
		self.protocol.closing()
		self.protocol = None

	def readable(self):
		if (len(self.recvbuff) > MAXLENGTH):
			raise (neubot.error("Buffer too big"))
		try:
			octets = self.connection.recv(8000)
		except neubot.error, (code, reason):
			if (code == errno.EPIPE):
				self.connection.close()
				return
			raise
		if (octets == ""):
			return
		self.recvbuff.append(octets)
		while (True):
			if (len(self.parsers) == 0):
				raise (neubot.error("Empty parser list"))
			parser = self.parsers[0]
			done = parser()
			if (not done):
				break
			self.parsers.popleft()

	def _parse_metadata(self):
		index = self.recvbuff.find("\r\n\r\n")
		if (index == -1):
			return (False)
		metadata = self.recvbuff.slice(index + 4)
		self.protocol.got_metadata(metadata)
		return (True)

	def _parse_bounded_body(self):
		while (True):
			amount = min(PIECE, self.bodylength)
			if (len(self.recvbuff) < amount):
				return (False)
			part = self.recvbuff.slice(amount)
			self.protocol.got_body_part(part)
			self.bodylength -= amount
			if (self.bodylength == 0):
				self.protocol.got_body()
				return (True)

	def _parse_unbounded_body(self):
		part = self.recvbuff.vent()
		self.protocol.got_body_part(part)
		return (False)

	def _parse_chunked_body(self):
		while (True):
			if (self.chunkstate == READING_LENGTH or
			    self.chunkstate == READING_END):
				index = self.recvbuff.find("\r\n")
				if (index == -1):
					return (False)
				line = self.recvbuff.slice(index + 2)
				if (self.chunkstate == READING_END):
					if (line != "\r\n"):
						raise (neubot.error
						    ("Protocol error"))
					self.chunkstate = READING_LENGTH
					continue
				try:
					vector = line.split()
					length = vector[0]
					self.chunklength = int(length, 16)
				except:
					self.chunklength = -1
				if (self.chunklength < 0):
					raise (neubot.error("Protocol error"))
				if (self.chunklength == 0):
					self.chunkstate = READING_TRAILERS
					continue
				self.chunkstate = READING_CHUNK
				continue
			if (self.chunkstate == READING_CHUNK):
				amount = min(PIECE, self.chunklength)
				if (len(self.recvbuff) < amount):
					return (False)
				part = self.recvbuff.slice(amount)
				self.protocol.got_body_part(part)
				self.chunklength -= amount
				if (self.chunklength == 0):
					self.chunkstate = READING_END
				continue
			if (self.chunkstate == READING_TRAILERS):
				index = self.recvbuff.find("\r\n")
				if (index == -1):
					return (False)
				line = self.recvbuff.slice(index + 2)
				if (line == "\r\n"):
					self.protocol.got_body()
					return (True)
				# Ignore other trailers
				continue
		raise (neubot.error("Reading chunks: internal error"))

	def writable(self):
		while (len(self.sendbuff) == 0):
			if (len(self.sendqueue) == 0):
				self.connection.unset_writable()
				self.protocol.sent_all()
				return
			filelike = self.sendqueue[0]
			octets = filelike.read()		# Yep, *all*
			if (octets == ""):
				self.sendqueue.popleft()
				continue
			self.sendbuff.set_content(octets)
		content = self.sendbuff.get_content()
		count = self.connection.send(content)
		if (count == 0):
			return
		self.sendbuff.advance(count)

	def attach(self, protocol):
		self.protocol = protocol

	def close(self):
		self.connection.close()

	def get_metadata(self):
		self.parsers.append(self._parse_metadata)

	def get_bounded_body(self, length):
		self.parsers.append(self._parse_bounded_body)
		self.bodylength = length

	def get_chunked_body(self):
		self.parsers.append(self._parse_chunked_body)
		self.chunkstate = READING_LENGTH

	def get_unbounded_body(self):
		self.parsers.append(self._parse_unbounded_body)

	def send(self, filelike):
		self.sendqueue.append(filelike)
		self.connection.set_writable()
