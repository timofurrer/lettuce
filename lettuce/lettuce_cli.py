#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <Lettuce - Behaviour Driven Development for python>
# Copyright (C) <2010-2011>  Gabriel Falcão <gabriel@nacaolivre.org>
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
import os
import sys
import optparse

import lettuce


def main(args=sys.argv[1:]):
    parser = optparse.OptionParser(
        usage="%prog [OPTION] [features ...] or type %prog -h (--help) for help",
        version=lettuce.version)

    parser.add_option("-b", "--base_path",
                      dest="base_path",
                      default="features",
                      help='The base path where to find the lettuce files')

    parser.add_option("-v", "--verbosity",
                      dest="verbosity",
                      default=4,
                      help='The verbosity level')

    parser.add_option("-s", "--scenarios",
                      dest="scenarios",
                      default=None,
                      help='Comma separated list of scenarios to run')

    parser.add_option("--with-xunit",
                      dest="enable_xunit",
                      action="store_true",
                      default=False,
                      help='Output JUnit XML test results to a file')

    parser.add_option("--xunit-file",
                      dest="xunit_file",
                      default=None,
                      type="string",
                      help='Write JUnit XML to this file. Defaults to '
                      'lettucetests.xml')

    parser.add_option("-a", "--abort-fail",
                      dest="abort_fail",
                      action="store_true",
                      default=False,
                      help='If one feature file fails this option will stop executing all the rest')

    options, args = parser.parse_args()
    feature_files = None
    if args:
        feature_files = [os.path.abspath(f) for f in args]

    try:
        options.verbosity = int(options.verbosity)
    except ValueError:
        pass

    runner = lettuce.Runner(
        base_path=os.path.abspath(options.base_path),
        feature_files=feature_files,
        scenarios=options.scenarios,
        verbosity=options.verbosity,
        enable_xunit=options.enable_xunit,
        xunit_filename=options.xunit_file,
        abort_fail=options.abort_fail
    )

    result = runner.run()
    if not result or result.steps != result.steps_passed:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
