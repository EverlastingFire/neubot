# neubot/network/connections.py
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

import errno
import socket
import ssl

import neubot

class socket_connection:
	def __init__(self, poller, socket):
		self.poller = poller
		self.socket = socket
		self.protocol = None

	def attach(self, protocol):
		self.protocol = protocol

	def set_readable(self):
		self.poller.set_readable(self)

	def set_writable(self):
		self.poller.set_writable(self)

	def unset_readable(self):
		self.poller.unset_readable(self)

	def unset_writable(self):
		self.poller.unset_writable(self)

	def recv(self, cnt):
		try:
			buf = self.socket.recv(cnt)
			if (not buf):
				raise (neubot.error(errno.EPIPE, "Broken pipe"))
			return (buf)
		except socket.error, (code, reason):
			if (code == errno.EWOULDBLOCK or
			    code == errno.EAGAIN):
				return ("")
			else:
				raise (neubot.error(code, reason))

	def send(self, buf):
		try:
			return (self.socket.send(buf))
		except socket.error, (code, reason):
			if (code == errno.EWOULDBLOCK or
			    code == errno.EAGAIN):
				return (0)
			else:
				raise (neubot.error(code, reason))

	def close(self):
		self.poller.close(self)

	def fileno(self):
		return (self.socket.fileno())

	def closing(self):
		self.protocol.closing()
		self.protocol = None
		self.socket.close()

	def readable(self):
		self.protocol.readable()

	def writable(self):
		self.protocol.writable()

class ssl_connection:
	def __init__(self, poller, ssl, handshake=True):
		self.poller = poller
		self.ssl = ssl
		self.handshake = handshake
		self.wantread = False
		self.wantwrite = False
		self.internalread = False
		self.internalwrite = False
		self.protocol = None

	def attach(self, protocol):
		self.protocol = protocol

	def set_readable(self):
		self.wantread = True
		if (not self.internalwrite):
			self.poller.set_readable(self)		# XXX

	def set_writable(self):
		self.wantwrite = True
		if (not self.internalread):
			self.poller.set_writable(self)		# XXX

	def unset_readable(self):
		self.wantread = False
		if (not self.internalread):
			self.poller.unset_readable(self)

	def unset_writable(self):
		self.wantwrite = False
		if (not self.internalwrite):
			self.poller.unset_writable(self)

	def recv(self, cnt):
		try:
			if (self.handshake):
				self.ssl.do_handshake()
				self.handshake = False
			buf = self.ssl.read(cnt)
			if (not buf):
				raise (neubot.error(errno.EPIPE, "Broken pipe"))
			return (buf)
		except ssl.SSLError, (code, reason):
			if (code == ssl.SSL_ERROR_WANT_READ or
			    code == ssl.SSL_ERROR_WANT_WRITE):
				if (code == ssl.SSL_ERROR_WANT_WRITE):
					#print 'enter internalwrite state'
					self.internalwrite = True
					self.poller.set_writable(self)
					self.poller.unset_readable(self) # XXX
				return ("")
			else:
				raise (neubot.error(code, reason))

	def send(self, buf):
		try:
			if (self.handshake):
				self.ssl.do_handshake()
				self.handshake = False
			return (self.ssl.write(buf))
		except ssl.SSLError, (code, reason):
			if (code == ssl.SSL_ERROR_WANT_READ or
			    code == ssl.SSL_ERROR_WANT_WRITE):
				if (code == ssl.SSL_ERROR_WANT_READ):
					#print 'enter internalread state'
					self.internalread = True
					self.poller.set_readable(self)
					self.poller.unset_writable(self) # XXX
				return (0)
			else:
				raise (neubot.error(code, reason))

	def close(self):
		self.poller.close(self)

	def fileno(self):
		return (self.ssl.fileno())

	def closing(self):
		self.protocol.closing()
		self.protocol = None
		self.ssl.close()

	def readable(self):
		if (self.internalwrite):		# FIXME
			return
		if (self.internalread):
			self.internalread = False
			if (not self.wantread):
				self.poller.unset_readable(self)
			if (self.wantwrite):
				self.poller.set_writable(self)
			#print 'leave internalread state'
			self.protocol.writable()
			return
		self.protocol.readable()

	def writable(self):
		if (self.internalread):			# FIXME
			return
		if (self.internalwrite):
			self.internalwrite = False
			if (not self.wantwrite):
				self.poller.unset_writable(self)
			if (self.wantread):
				self.poller.set_readable(self)
			#print 'leave internalwrite state'
			self.protocol.readable()
			return
		self.protocol.writable()
