# -*- coding: utf-8 -*-
# <Lettuce - Behaviour Driven Development for python>
# Copyright (C) <2010-2012>  Gabriel Falcão <gabriel@nacaolivre.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import re
import os
import imp
import sys
import codecs
import fnmatch
import zipfile

from glob import glob
from os.path import abspath, join, dirname, curdir, exists
from lettuce.exceptions import BasePathNotFoundError, StepLoadingError, FeatureLoadingError

def find_base_path(base_path):
    feature_file = None
    if not os.path.isdir(base_path):
        if os.path.isfile(base_path) and os.path.exists(base_path): # backwards compatibility of the single feature files
            feature_file = base_path
            base_path    = os.path.dirname(base_path)
        else:
            raise BasePathNotFoundError(base_path)
    return base_path, feature_file

class FeatureLoader(object):
    """Loader class responsible for findind features and step
    definitions along a given path on filesystem"""
    def __init__(self, base_dir):
        self.base_dir = FileSystem.abspath(base_dir)

    def find_and_load_step_definitions(self):
        files = FileSystem.locate(self.base_dir, '*.py')
        for filename in files:
            root = FileSystem.dirname(filename)
            sys.path.insert(0, root)
            to_load = FileSystem.filename(filename, with_extension=False)
            try:
                module = __import__(to_load)
            except ValueError, e:
                import traceback
                err_msg = traceback.format_exc(e)
                if 'empty module name' in err_msg.lower():
                    continue
                else:
                    raise e

            reload(module)  # always take fresh meat :)
            sys.path.remove(root)

    def load_feature_files(self, paths):
        feature_files = []
        if paths:
            if os.path.isfile(unicode(paths)):
                feature_files.append(paths)
            else:
                for f in paths:
                    if os.path.isfile(f) and os.path.exists(f):
                        feature_files.append(f)
                    elif os.path.isdir(f) and os.path.exists(f):
                        feature_files.extend(self.find_feature_files(f))
                    else:
                        raise FeatureLoadingError( f )
        return feature_files

    def find_feature_files(self, path=None):
        if not path:
            path = self.base_dir
        return FileSystem.locate(path, "*.feature")

class FileSystem(object):
    """File system abstraction, mainly used for indirection, so that
    lettuce can be well unit-tested :)
    """
    stack = []

    def __init__(self):
        self.stack = []

    @classmethod
    def _import(cls, name):
        sys.path.insert(0, cls.current_dir())
        fp, pathname, description = imp.find_module(name)

        try:
            module = imp.load_module(name, fp, pathname, description)
            sys.path.remove(cls.current_dir())
            return module
        finally:
            # Since we may exit via an exception, close fp explicitly.
            if fp:
                fp.close()

    @classmethod
    def pushd(cls, *path):
        """Change current dir to `path`, adding it to a stack. Can be
        undone by calling FileSystem.popd()"""

        path = cls.join(*path)
        if not len(cls.stack):
            cls.stack.append(cls.current_dir())

        cls.stack.append(path)
        os.chdir(path)

    @classmethod
    def popd(cls):
        """Go back one path in path stack"""
        if cls.stack:
            cls.stack.pop()
            if cls.stack:
                os.chdir(cls.stack[-1])

    @classmethod
    def filename(cls, path, with_extension=True):
        """Returns only the filename from a full path. If the argument
        with_extension is False, return the filename without
        extension.

        Examples::

        >>> from lettuce.fs import FileSystem
        >>> assert FileSystem.filename('/full/path/to/some_file.py') == 'some_file.py'
        >>> assert FileSystem.filename('/full/path/to/some_file.py', False) == 'some_file'

        """
        fname = os.path.split(path)[1]
        if not with_extension:
            fname = os.path.splitext(fname)[0]

        return fname

    @classmethod
    def exists(cls, path):
        """Return True if `path`exists"""
        return exists(path)

    @classmethod
    def mkdir(cls, path):
        """Create paths recursively, ignore already created dirs

        Example:
            >>> from lettuce.fs import FileSystem
            >>> FileSystem.mkdir('~/a/lot/of/nested/dirs')
        """
        try:
            os.makedirs(path)
        except OSError, e:
            # ignore if path already exists
            if e.errno not in (17, ):
                raise e
            else:
                if not os.path.isdir(path):
                    # but the path must be a dir to ignore its creation
                    raise e

    @classmethod
    def current_dir(cls, path=""):
        '''Returns the absolute path for current dir, also join the
        current path with the given, if so.'''
        to_return = cls.abspath(curdir)
        if path:
            return cls.join(to_return, path)

        return to_return

    @classmethod
    def abspath(cls, path):
        '''Returns the absolute path for the given path.'''
        return abspath(path)

    @classmethod
    def relpath(cls, path):
        '''Returns the absolute path for the given path.'''
        current_path = cls.current_dir()
        absolute_path = cls.abspath(path)
        return re.sub("^" + re.escape(current_path), '', absolute_path).lstrip("/")

    @classmethod
    def join(cls, *args):
        '''Returns the concatenated path for the given arguments.'''
        return join(*args)

    @classmethod
    def dirname(cls, path):
        '''Returns the directory name for the given file.'''
        return cls.abspath(dirname(path))

    @classmethod
    def walk(cls, path):
        '''Walks through filesystem'''
        return os.walk(path)

    @classmethod
    def locate(cls, path, match, recursive=True, sort=True):
        """Locate files recursively in a given path"""
        root_path = cls.abspath(path)
        return_files = []
        if recursive:
            for path, dirs, files in cls.walk(root_path):
                for filename in fnmatch.filter(files, match):
                    return_files.append(cls.join(path, filename))
        else:
            return_files = glob(cls.join(root_path, match))
        if sort and return_files:
          return_files.sort( )
        return return_files

    @classmethod
    def extract_zip(cls, filename, base_path='.', verbose=False):
        """Extracts a zip file into `base_path`"""
        base_path = cls.abspath(base_path)
        output = lambda x: verbose and sys.stdout.write("%s\n" % x)

        cls.pushd(base_path)
        zfile = zipfile.ZipFile(filename)

        output("Extracting files to %s" % base_path)
        for file_name in zfile.namelist():
            try:
                output("  -> Unpacking %s" % file_name)
                f = cls.open_raw(file_name, 'w')
                f.write(zfile.read(file_name))
                f.close()
            except IOError:
                output("---> Creating directory %s" % file_name)
                cls.mkdir(file_name)

        cls.popd()

    @classmethod
    def open(cls, name, mode):
        """Opens a file as utf-8"""
        path = name
        if not os.path.isabs(path):
            path = cls.current_dir(name)

        return codecs.open(path, mode, 'utf-8')

    @classmethod
    def open_raw(cls, name, mode):
        """Opens a file without specifying encoding"""
        path = name
        if not os.path.isabs(path):
            path = cls.current_dir(name)

        return open(path, mode)
