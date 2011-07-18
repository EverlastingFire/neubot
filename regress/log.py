#!/usr/bin/env python

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
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
#

#
# This is the old testing code for the logger...
# the code below screams for deletion and an unit
# test would be more than welcome.
#

import sys
import traceback

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.log import LOG
from neubot import compat

if __name__ == "__main__":
    LOG.start("Testing the in-progress feature")
    LOG.progress("...")
    LOG.progress()
    LOG.complete("success!")

    LOG.verbose()

    LOG.error("testing neubot logger -- This is an error message")
    LOG.warning("testing neubot logger -- This is an warning message")
    LOG.info("testing neubot logger -- This is an info message")
    LOG.debug("testing neubot logger -- This is a debug message")
    print compat.json.dumps(LOG.listify())

    try:
        raise Exception("Testing LOG.exception")
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        LOG.exception()
        LOG.exception(func=LOG.warning)

    LOG.start("Testing the in-progress feature")
    LOG.progress("...")
    LOG.progress()
    LOG.complete("success!")

    LOG.oops("Testing the new oops feature")

    LOG.redirect()

    LOG.error("testing neubot logger -- This is an error message")
    LOG.warning("testing neubot logger -- This is an warning message")
    LOG.info("testing neubot logger -- This is an info message")
    LOG.debug("testing neubot logger -- This is a debug message")