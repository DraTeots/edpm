import os


class GeneratorStep(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def gen_bash(self):
        """Generates bash piece of code"""
        raise NotImplementedError()

    def gen_csh(self):
        """Generates csh piece code"""
        raise NotImplementedError()

    def update_python_env(self):
        """Sets environment internally for python"""
        raise NotImplementedError()

    @staticmethod
    def is_in_path_env(path):
        """Sets environment internally for python"""
        path_tokens = os.environ.get('PATH', '').split(os.pathsep)
        return path in path_tokens


class EnvAppend(GeneratorStep):
    """Appends environment variables like PATH or LD_LIBRARY_PATH"""

    def __init__(self, name, value):
        super(EnvAppend, self).__init__(name, value)

    def gen_bash(self):
        """Generates bash piece of code"""

        # Here is the right way to APPEND in bash:
        # PATH = "${PATH:+${PATH}:}$HOME/bin"
        # https://unix.stackexchange.com/a/415028/109031
        ret_str = "export {name}=${{{name}:+${{{name}}}:}}{value}\n"

        return ret_str.format(name=self.name, value=self.value)

    def gen_csh(self):
        """Generates csh piece code"""

        ret_str = (
            '\n'
            '# Make sure {name} is set\n'
            'if ( ! $?{name} ) then\n'
            '    setenv {name} "{value}"\n'
            'else\n'
            '    setenv {name} ${{{name}}}:"{value}"\n'
            'endif')

        return ret_str.format(name=self.name, value=self.value)

    def update_python_env(self):
        """Sets environment internally for python"""
        print("   update_env:  append ${} by '{}'".format(self.name, self.value))
        if self.name in os.environ.keys():
            os.environ[self.name] += os.pathsep + self.value
        else:
            os.environ[self.name] = self.value


class EnvPrepend(GeneratorStep):
    """Prepends environment variables like PATH or LD_LIBRARY_PATH"""

    def __init__(self, name, value):
        super(EnvPrepend, self).__init__(name, value)

    def gen_bash(self):
        """Generates bash piece of code"""

        # Here is the right way to prepend in bash:
        # #PATH = "$HOME/bin${PATH:+:${PATH}}"
        # https://unix.stackexchange.com/a/415028/109031
        ret_str = "export {name}={value}${{{name}:+:${{{name}}}}}\n"

        # ret_str = (
        #     '\n'
        #     '# Make sure {name} is set\n'
        #     'if [ -z "${name}" ]; then\n'
        #     '    export {name}="{value}"\n'
        #     'else\n'
        #     '    export {name}="{value}":${name}\n'
        #     'fi')

        return ret_str.format(name=self.name, value=self.value)

    def gen_csh(self):
        """Generates csh piece code"""

        ret_str = (
            '\n'
            '# Make sure {name} is set\n'
            'if ( ! $?{name} ) then\n'
            '    setenv {name} "{value}"\n'
            'else\n'
            '    setenv {name} "{value}":${{{name}}}\n'
            'endif')

        return ret_str.format(name=self.name, value=self.value)

    def update_python_env(self):
        """Sets environment internally for python"""

        print("   update_env: prepend ${} by '{}'".format(self.name, self.value))
        if self.name in os.environ.keys():
            os.environ[self.name] = self.value + os.pathsep + os.environ[self.name]
        else:
            os.environ[self.name] = self.value


class EnvSet(GeneratorStep):
    """Sets environment variables like PATH or LD_LIBRARY_PATH"""

    def __init__(self, name, value):
        super(EnvSet, self).__init__(name, value)

    def gen_bash(self):
        """Generates bash piece of code"""
        return 'export {name}="{value}"'.format(name=self.name, value=self.value)

    def gen_csh(self):
        """Generates csh piece code"""
        return 'setenv {name} "{value}"'.format(name=self.name, value=self.value)

    def update_python_env(self):
        """Sets environment internally for python"""

        print("   update_env:     set ${} = '{}'".format(self.name, self.value))
        os.environ[self.name] = self.value


class EnvRawText(GeneratorStep):
    def __init__(self, sh_text, csh_text, python_env):
        """ Function allows to

        :param sh_text: Text for Bash generated script
        :param csh_text: Text for CSH generated script
        :param python_env: The function that manipulates python environment right
        """

        super(EnvRawText, self).__init__('', '')
        self.sh_text = sh_text
        self.csh_text = csh_text
        self.python_env = python_env

    def gen_bash(self):
        """Generates bash piece of code"""
        return self.sh_text

    def gen_csh(self):
        """Generates csh piece code"""
        return self.csh_text

    def update_python_env(self):
        """Sets environment internally for python"""
        print("   update_env: EnvRawText step will update env")
        self.python_env()


class EnvComment(GeneratorStep):
    def __init__(self, text):
        """
        Adds comment to generated script

        :param text: The comment text
        """
        super(EnvComment, self).__init__('', '')
        self.text = text

    def gen_bash(self):
        """Generates bash piece of code"""
        return self.text

    def gen_csh(self):
        """Generates csh piece code"""
        return self.text

    def update_python_env(self):
        """Sets environment internally for python"""
        pass    # Just nothing to do!

# edpm/engine/steps.py

class CmakeSet(GeneratorStep):
    """
    A CMake directive to set(VAR VALUE).
    We'll implement gen_cmake_line() to produce a line in EDPMConfig.cmake.
    For shell/csh we do nothing or just a comment.
    """
    def __init__(self, name, value):
        super().__init__(name, value)

    def gen_bash(self):
        # We do nothing for shell. Could add a comment or skip
        return f""

    def gen_csh(self):
        # Same idea for csh
        return f""

    def gen_cmake_line(self):
        # We'll assume string or path usage. Adjust as needed:
        return f'set({self.name} "{self.value}" CACHE PATH "Set by EDPM")'


class CmakePrefixPath(EnvPrepend):
    """
    A CMake directive to prepend a path to a semicolon-delimited variable
    (like CMAKE_PREFIX_PATH).
    """
    def __init__(self, path):
        super().__init__("CMAKE_PREFIX_PATH", path)


    def gen_cmake_line(self):
        # We'll generate something like:
        # if(NOT DEFINED var) set(var "") endif()
        # list(APPEND var "path/to/dir")
        #
        # or you could do the "prepend" approach. Some folks prefer "APPEND" for everything,
        # but let's emulate the EDPM approach:
        return f'if(NOT DEFINED CMAKE_PREFIX_PATH)\n'\
               f'   set(CMAKE_PREFIX_PATH "")\n'\
               f'endif()\n'\
               f'list(INSERT CMAKE_PREFIX_PATH 0 "{self.value}")'.strip()


class CmakeLine(GeneratorStep):
    """
    Allows a raw line to be inserted into EDPMConfig.cmake, e.g.
    'find_package(Clhep REQUIRED)'
    """
    def __init__(self, cmake_text):
        super().__init__(name="", value="")
        self.cmake_text = cmake_text

    def gen_bash(self):
        return ""

    def gen_csh(self):
        return ""

    def gen_cmake_line(self):
        return self.cmake_text
