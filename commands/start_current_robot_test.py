import json
import re
import os
import platform
import sublime, sublime_plugin
import subprocess

class StartCurrentRobotTestCommand(sublime_plugin.TextCommand):
    """ Run the current test case with Robot.

    The current test case is found by checking the position of the first selection region.
    The algorithm will first check that the position is in the Testcase-table and will then
    look backwards line by line for the next line which matches the definition of a Testcase-name.

    Uses settings from Robot Framework Assistant (Robot.sublime-settings):
        "robot_framework_workspace": "path_were_to_run_Robot"
        "robot_framework_output_path": "path_where_to_put_the_files_generated_by_Robot"
        "robot_framework_keep_console": [true|false] (only Windows, default: false)
        "robot_framework_consolewidth": <width>

    Example how to bind the function to a key:
        { "keys": ["f8"],
            "command": "start_current_robot_test"
        },
        { "keys": ["shift+f8"],
            "command": "start_current_robot_test",
            "args": {"repeat": true}
        }
    """

    table_regex = re.compile(r'^\s{0,1}\*+\s{0,1}(.+?)\s{0,1}\*')
    keyword_regex = re.compile(r'^(\|\s)?(?P<keyword>[^\s\|]+[^\|]*?)(\s*|\s*\|)?$')
    prev_test_file = 'previousTest.json'

    def run(self, edit, repeat=False):
        """ Runs current test with Robot, or repeats last test.

        Arguments:
        repeat -- if true, the last test will be repeated, instead of running current test
        """
        if repeat:
            self.repeat_previous_started_test()
        else:
            self.run_current_test()

    def run_current_test(self):
        line = self.get_current_line()
        table_name = self.get_table_name(line)
        if self.is_table_testcase(table_name):
            testcase_name = self.get_keyword_name(line)
            suite_name = self.get_suite_name()
            self.start_robot(testcase_name, suite_name)
            previous_started_test = {'testcase': testcase_name, 'suite': suite_name}
            with open(self.prev_test_file, 'w') as jsonfile:
                json.dump(previous_started_test, jsonfile)
        else:
            self.print_and_send('no testcase')

    def repeat_previous_started_test(self):
        self.print_and_send('repeating')
        with open(self.prev_test_file, 'r') as jsonfile:
            previous_started_test = json.load(jsonfile)
        testcase_name = previous_started_test['testcase']
        suite_name = previous_started_test['suite']
        self.start_robot(testcase_name, suite_name)

    def start_robot(self, testcase, suite):
        settings = sublime.load_settings('Robot.sublime-settings')
        self.print_and_send("starting Test '{}' in Suite '{}'".format(testcase, suite))
        work_path = settings.get('robot_framework_workspace')
        output_path = settings.get('robot_framework_output_path')
        consolewidth = settings.get('robot_framework_consolewidth')
        if platform.system() == 'Windows':
            cmd = 'cmd '
            cmd += '/k ' if settings.get('robot_framework_keep_console') else '/c '
            cmd += 'pybot '
        else:
            cmd = 'python -m robot.run '
        if consolewidth:
            cmd += '--consolewidth %s ' % consolewidth
        cmd += '--test "%s" ' % testcase
        cmd += '--suite "%s" ' % suite
        cmd += '--outputdir %s ' % output_path
        cmd += '--debugfile debug.txt '
        cmd += '.'
        subprocess.Popen(cmd, cwd=work_path)

    def print_and_send(self, message):
        print(message)
        sublime.status_message(message)

    def get_current_line(self):
        first_region = self.view.sel()[0]
        return self.view.line(first_region.begin())

    def row_to_line(self, row):
        point = self.view.text_point(row, 0)
        return self.view.line(point)

    def get_table_name(self, line):
        row, _ = self.view.rowcol(line.begin())
        found = None
        while not found and row >= 0:
            line_str = self.view.substr(self.row_to_line(row))
            match = self.table_regex.search(line_str)
            if match:
                found = match.group(1)
            row -= 1
        return found

    def is_table_testcase(self, table_name):
        return table_name.upper() in ['TEST CASES', 'TEST CASE', 'TESTCASES', 'TESTCASE']

    def get_keyword_name(self, line):
        row, _ = self.view.rowcol(line.begin())
        found = None
        while not found and row >= 0:
            line_str = self.view.substr(self.row_to_line(row))
            match = self.keyword_regex.search(line_str)
            if match:
                found = match.group('keyword')
            row -= 1
        return found

    def get_suite_name(self):
        file_name = self.view.file_name()
        suite_name = None
        if file_name.endswith('.robot') or file_name.endswith('.txt'):
            p_stop = file_name.rfind('.')
            p_start = file_name.rfind(os.sep) + 1
            suite_name = file_name[p_start:p_stop]
        return suite_name
