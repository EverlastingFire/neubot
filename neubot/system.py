# neubot/system.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

''' System dependent routines '''

# NB: This code is currently being refactored.

import os

if os.name == "nt":
    from neubot.system_win32 import change_dir
    from neubot.system_win32 import go_background
    from neubot.system_win32 import drop_privileges
    from neubot.system_win32 import redirect_to_dev_null
    from neubot.system_win32 import _get_profile_dir
    from neubot.system_win32 import _get_pidfile_dir
    from neubot.system_win32 import _want_rwx_dir
    from neubot.system_win32 import _want_rw_file
    from neubot.system_win32 import get_background_logger
elif os.name == "posix":
    from neubot.system_posix import change_dir
    from neubot.system_posix import go_background
    from neubot.system_posix import drop_privileges
    from neubot.system_posix import redirect_to_dev_null
    from neubot.system_posix import _get_profile_dir
    from neubot.system_posix import _get_pidfile_dir
    from neubot.system_posix import _want_rwx_dir
    from neubot.system_posix import _want_rw_file
    from neubot.system_posix import get_background_logger
else:
    raise RuntimeError("Your system is not supported")

def write_pidfile():
    ''' Write pidfile '''
    dirname = _get_pidfile_dir()
    if dirname:
        pathname = os.sep.join([ dirname, "neubot.pid" ])
        filep = open(pathname, "w")
        filep.write("%d\n" % os.getpid())
        filep.close()

def get_default_database_path():
    ''' Get default database path '''
    return os.sep.join([ _get_profile_dir(), "database.sqlite3" ])

def check_database_path(pathname):
    ''' Make sure database path is OK '''
    pathname = os.path.abspath(pathname)
    _want_rwx_dir(os.path.dirname(pathname))
    _want_rw_file(pathname)
    return pathname