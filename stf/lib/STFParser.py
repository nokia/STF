"""Configuration file parser.

A setup file consists of sections, lead by a "[section]" header,
and followed by "name: value" entries, with continuations and such in
the style of RFC 822.

The option values can contain format strings which refer to other values in
the same section, or values in a special [DEFAULT] section.

For example:

    something: %(dir)s/whatever

would resolve the "%(dir)s" to the value of dir.  All reference
expansions are done late, on demand.

Intrinsic defaults can be specified by passing them into the
ConfigParser constructor as a dictionary.

class:

ConfigParser -- responsible for parsing a list of
                configuration files, and managing the parsed database.

    methods:

    __init__(defaults=None)
        create the parser and specify a dictionary of intrinsic defaults.  The
        keys must be strings, the values must be appropriate for %()s string
        interpolation.  Note that `__name__' is always an intrinsic default;
        its value is the section's name.

    sections()
        return all the configuration section names, sans DEFAULT

    hasSection(section)
        return whether the given section exists

    hasOption(section, option)
        return whether the given option exists in the given section

    options(section)
        return list of configuration options for the named section

    read(filenames)
        read and parse the list of named configuration files, given by
        name.  A single filename is also allowed.  Non-existing files
        are ignored.  Return list of successfully read files.

    readfp(fp, filename=None)
        read and parse one configuration file, given as a file object.
        The filename defaults to fp.name; it is only used in error
        messages (if fp has no `name' attribute, the string `<???>' is used).

    get(section, option, raw=False, vars=None)
        return a string value for the named option.  All % interpolations are
        expanded in the return values, based on the defaults passed into the
        constructor and the DEFAULT section.  Additional substitutions may be
        provided using the `vars' argument, which must be a dictionary whose
        contents override any pre-existing defaults.

    getInt(section, options)
        like get(), but convert value to an integer

    getFloat(section, options)
        like get(), but convert value to a float

    getBoolean(section, options)
        like get(), but convert value to a boolean (currently case
        insensitively defined as 0, false, no, off for False, and 1, true,
        yes, on for True).  Returns False or True.

    items(section, raw=False, vars=None)
        return a list of tuples with (name, value) for each option
        in the section.

    removeSection(section)
        remove the given file section and all its options

    removeOption(section, option)
        remove the given option from the given section

    set(section, option, value)
        set the given option

    write(fp)
        write the configuration state in .ini format
"""

try:
    from collections import OrderedDict as _default_dict
except ImportError:
    # fallback for setup.py which hasn't yet built _collections
    _default_dict = dict

import re
import os

__all__ = ["NoSectionError", "DuplicateSectionError", "NoOptionError",
           "InterpolationError", "InterpolationDepthError",
           "InterpolationSyntaxError", "ParsingError",
           "MissingSectionHeaderError",
           "ConfigParser", "SafeConfigParser", "RawConfigParser",
           "DEFAULTSECT", "MAX_INTERPOLATION_DEPTH"]

DEFAULTSECT = "DEFAULT"

MAX_INTERPOLATION_DEPTH = 10


class IniItem(object):
    def __init__(self, line):
        self.line = line
        #None represent a comment or continuation line or blank, anyway, not a section header or key value pair
        self.section = None
        self.key = None


# exception classes
class Error(Exception):
    """Base class for ConfigParser exceptions."""

    def _get_message(self):
        """Getter for 'message'; needed only to override deprecation in
        BaseException."""
        return self.__message

    def _set_message(self, value):
        """Setter for 'message'; needed only to override deprecation in
        BaseException."""
        self.__message = value

    # BaseException.message has been deprecated since Python 2.6.  To prevent
    # DeprecationWarning from popping up over this pre-existing attribute, use
    # a new property that takes lookup precedence.
    message = property(_get_message, _set_message)

    def __init__(self, msg=''):
        self.message = msg
        Exception.__init__(self, msg)

    def __repr__(self):
        return self.message

    __str__ = __repr__

class NoSectionError(Error):
    """Raised when no section matches a requested option."""

    def __init__(self, section):
        Error.__init__(self, 'No section: %r' % (section,))
        self.section = section
        self.args = (section, )

class DuplicateSectionError(Error):
    """Raised when a section is multiply-created."""

    def __init__(self, section):
        Error.__init__(self, "Section %r already exists" % section)
        self.section = section
        self.args = (section, )

class NoOptionError(Error):
    """A requested option was not found."""

    def __init__(self, option, section):
        Error.__init__(self, "No option %r in section: %r" %
                       (option, section))
        self.option = option
        self.section = section
        self.args = (option, section)

class InterpolationError(Error):
    """Base class for interpolation-related exceptions."""

    def __init__(self, option, section, msg):
        Error.__init__(self, msg)
        self.option = option
        self.section = section
        self.args = (option, section, msg)

class InterpolationMissingOptionError(InterpolationError):
    """A string substitution required a setting which was not available."""

    def __init__(self, option, section, rawval, reference):
        msg = ("Bad value substitution:\n"
               "\tsection: [%s]\n"
               "\toption : %s\n"
               "\tkey    : %s\n"
               "\trawval : %s\n"
               % (section, option, reference, rawval))
        InterpolationError.__init__(self, option, section, msg)
        self.reference = reference
        self.args = (option, section, rawval, reference)

class InterpolationSyntaxError(InterpolationError):
    """Raised when the source text into which substitutions are made
    does not conform to the required syntax."""

class InterpolationDepthError(InterpolationError):
    """Raised when substitutions are nested too deeply."""

    def __init__(self, option, section, rawval):
        msg = ("Value interpolation too deeply recursive:\n"
               "\tsection: [%s]\n"
               "\toption : %s\n"
               "\trawval : %s\n"
               % (section, option, rawval))
        InterpolationError.__init__(self, option, section, msg)
        self.args = (option, section, rawval)

class ParsingError(Error):
    """Raised when a configuration file does not follow legal syntax."""

    def __init__(self, filename):
        Error.__init__(self, 'File contains parsing errors: %s' % filename)
        self.filename = filename
        self.errors = []
        self.args = (filename, )

    def append(self, lineno, line):
        self.errors.append((lineno, line))
        self.message += '\n\t[line %2d]: %s' % (lineno, line)

class MissingSectionHeaderError(ParsingError):
    """Raised when a key-value pair is found before any section header."""

    def __init__(self, filename, lineno, line):
        Error.__init__(
            self,
            'File contains no section headers.\nfile: %s, line: %d\n%r' %
            (filename, lineno, line))
        self.filename = filename
        self.lineno = lineno
        self.line = line
        self.args = (filename, lineno, line)


class RawConfigParser(object):
    def __init__(self, defaults=None, dict_type=_default_dict,
                 allow_no_value=False):
        self._dict = dict_type
        self._sections = self._dict()
        self._defaults = self._dict()
        self._lines = []
        if allow_no_value:
            self._optcre = self.OPTCRE_NV
        else:
            self._optcre = self.OPTCRE
        if defaults:
            for key, value in defaults.items():
                self._defaults[self.optionxform(key)] = value

    def defaults(self):
        return self._defaults

    def sections(self):
        """Return a list of section names, excluding [DEFAULT]"""
        # self._sections will never have [DEFAULT] in it
        return self._sections.keys()

    def addSection(self, section):
        """Create a new section in the configuration.

        Raise DuplicateSectionError if a section by the specified name
        already exists. Raise ValueError if name is DEFAULT or any of it's
        case-insensitive variants.
        """
        if section.lower() == "default":
            raise ValueError('Invalid section name: %s' % section)

        if section in self._sections:
            raise DuplicateSectionError(section)
        self._sections[section] = self._dict()

    def hasSection(self, section):
        """Indicate whether the named section is present in the configuration.

        The DEFAULT section is not acknowledged.
        """
        return section in self._sections

    def options(self, section):
        """Return a list of option names for the given section name."""
        try:
            opts = self._sections[section].copy()
        except KeyError:
            raise NoSectionError(section)
        opts.update(self._defaults)
        if '__name__' in opts:
            del opts['__name__']
        return opts.keys()

    def read(self, filenames):
        """Read and parse a filename or a list of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify a list of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the list will be read.  A single
        filename may also be given.

        Return list of successfully read files.
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]
        read_ok = []
        for filename in filenames:
            try:
                fp = open(filename)
            except IOError:
                continue
            self._read(fp, filename)
            fp.close()
            read_ok.append(filename)
        return read_ok

    def readfp(self, fp, filename=None):
        """Like read() but the argument must be a file-like object.

        The `fp' argument must have a `readline' method.  Optional
        second argument is the `filename', which if not given, is
        taken from fp.name.  If fp has no `name' attribute, `<???>' is
        used.

        """
        if filename is None:
            try:
                filename = fp.name
            except AttributeError:
                filename = '<???>'
        self._read(fp, filename)

    def get(self, section, option):
        opt = self.optionxform(option)
        if section not in self._sections:
            if section != DEFAULTSECT:
                raise NoSectionError(section)
            if opt in self._defaults:
                return self._defaults[opt]
            else:
                raise NoOptionError(option, section)
        elif opt in self._sections[section]:
            return self._sections[section][opt]
        elif opt in self._defaults:
            return self._defaults[opt]
        else:
            raise NoOptionError(option, section)

    def items(self, section):
        try:
            d2 = self._sections[section]
        except KeyError:
            if section != DEFAULTSECT:
                raise NoSectionError(section)
            d2 = self._dict()
        d = self._defaults.copy()
        d.update(d2)
        if "__name__" in d:
            del d["__name__"]
        return d.items()

    def _get(self, section, conv, option):
        return conv(self.get(section, option))

    def getInt(self, section, option):
        return self._get(section, int, option)

    def getFloat(self, section, option):
        return self._get(section, float, option)

    _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def getBoolean(self, section, option):
        v = self.get(section, option)
        if v.lower() not in self._boolean_states:
            raise ValueError('Not a boolean: %s' % v)
        return self._boolean_states[v.lower()]

    def optionxform(self, optionstr):
        return optionstr.lower()

    def hasOption(self, section, option):
        """Check for the existence of a given option in a given section."""
        if not section or section == DEFAULTSECT:
            option = self.optionxform(option)
            return option in self._defaults
        elif section not in self._sections:
            return False
        else:
            option = self.optionxform(option)
            return (option in self._sections[section]
                    or option in self._defaults)

    def set(self, section, option, value=None):
        """Set an option."""
        if not section or section == DEFAULTSECT:
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise NoSectionError(section)
        sectdict[self.optionxform(option)] = value

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    key = " = ".join((key, str(value).replace('\n', '\n\t')))
                fp.write("%s\n" % (key))
            fp.write("\n")

    def removeOption(self, section, option):
        """Remove an option."""
        if not section or section == DEFAULTSECT:
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise NoSectionError(section)
        option = self.optionxform(option)
        existed = option in sectdict
        if existed:
            del sectdict[option]
        return existed

    def removeSection(self, section):
        """Remove a file section."""
        existed = section in self._sections
        if existed:
            del self._sections[section]
        return existed

    #
    # Regular expressions for parsing section headers and options.
    #
    SECTCRE = re.compile(
        r'\['                                 # [
        r'(?P<header>[^]]+)'                  # very permissive!
        r'\]'                                 # ]
        )
    OPTCRE = re.compile(
        r'(?P<option>[^:=\s][^:=]*)'          # very permissive!
        r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
                                              # followed by separator
                                              # (either : or =), followed
                                              # by any # space/tab
        r'(?P<value>.*)$'                     # everything up to eol
        )
    OPTCRE_NV = re.compile(
        r'(?P<option>[^:=\s][^:=]*)'          # very permissive!
        r'\s*(?:'                             # any number of space/tab,
        r'(?P<vi>[:=])\s*'                    # optionally followed by
                                              # separator (either : or
                                              # =), followed by any #
                                              # space/tab
        r'(?P<value>.*))?$'                   # everything up to eol
        )

    def _read(self, fp, fpname):
        """Parse a sectioned setup file.

        The sections in setup file contains a title line at the top,
        indicated by a name in square brackets (`[]'), plus key/value
        options lines, indicated by `name: value' format lines.
        Continuations are represented by an embedded newline then
        leading whitespace.  Blank lines, lines beginning with a '#',
        and just about everything else are ignored.
        """
        cursect = None                        # None, or a dictionary
        optname = None
        lineno = 0
        e = None                              # None, or an exception
        while True:
            line = fp.readline()
            if not line:
                break

            item_ins = IniItem(line)
            self._lines.append(item_ins)

            lineno = lineno + 1
            # comment or blank line?
            if line.strip() == '' or line[0] in '#;':
                continue
            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                # no leading whitespace
                continue
            # continuation line?
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    cursect[optname].append(value)
            # a section header or option header?
            else:
                # is it a section header?
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        cursect = self._sections[sectname]
                    elif sectname == DEFAULTSECT:
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        cursect['__name__'] = sectname
                        self._sections[sectname] = cursect
                        item_ins.section = cursect['__name__']
                        item_ins.key = '__name__'
                    # So sections can't start with a continuation line
                    optname = None
                # no section header in the file?
                elif cursect is None:
                    raise MissingSectionHeaderError(fpname, lineno, line)
                # an option line?
                else:
                    mo = self._optcre.match(line)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        optname = self.optionxform(optname.rstrip())
                        # This check is fine because the OPTCRE cannot
                        # match if it would set optval to None
                        if optval is not None:
                            if vi in ('=', ':') and ';' in optval:
                                # ';' is a comment delimiter only if it follows
                                # a spacing character
                                pos = optval.find(';')
                                if pos != -1 and optval[pos-1].isspace():
                                    optval = optval[:pos]
                            optval = optval.strip()
                            # allow empty values
                            if optval == '""':
                                optval = ''
                            cursect[optname] = [optval]
                        else:
                            # valueless option handling
                            cursect[optname] = optval
                        item_ins.section = cursect['__name__']
                        item_ins.key = optname
                    else:
                        # a non-fatal parsing error occurred.  set up the
                        # exception but keep going. the exception will be
                        # raised at the end of the file and will contain a
                        # list of all bogus lines
                        if not e:
                            e = ParsingError(fpname)
                        e.append(lineno, repr(line))
        # if any parsing errors occurred, raise an exception
        if e:
            raise e

        # join the multi-line values collected while reading
        all_sections = [self._defaults]
        all_sections.extend(self._sections.values())
        for options in all_sections:
            for name, val in options.items():
                if isinstance(val, list):
                    options[name] = '\n'.join(val)

import UserDict as _UserDict

class _Chainmap(_UserDict.DictMixin):
    """Combine multiple mappings for successive lookups.

    For example, to emulate Python's normal lookup sequence:

        import __builtin__
        pylookup = _Chainmap(locals(), globals(), vars(__builtin__))
    """

    def __init__(self, *maps):
        self._maps = maps

    def __getitem__(self, key):
        for mapping in self._maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(key)

    def keys(self):
        result = []
        seen = set()
        for mapping in self._maps:
            for key in mapping:
                if key not in seen:
                    result.append(key)
                    seen.add(key)
        return result

class ConfigParser(RawConfigParser):

    def get(self, section, option, raw=False, vars=None):
        """Get an option value for a given section.

        If `vars' is provided, it must be a dictionary. The option is looked up
        in `vars' (if provided), `section', and in `defaults' in that order.

        All % interpolations are expanded in the return values, unless the
        optional argument `raw' is true. Values for interpolation keys are
        looked up in the same manner as the option.

        The section DEFAULT is special.
        """
        sectiondict = {}
        try:
            sectiondict = self._sections[section]
        except KeyError:
            if section != DEFAULTSECT:
                raise NoSectionError(section)
        # Update with the entry specific variables
        vardict = {}
        if vars:
            for key, value in vars.items():
                vardict[self.optionxform(key)] = value
        d = _Chainmap(vardict, sectiondict, self._defaults)
        option = self.optionxform(option)
        try:
            value = d[option]
        except KeyError:
            raise NoOptionError(option, section)

        if raw or value is None:
            return value
        else:
            return self._interpolate(section, option, value, d)

    def items(self, section, raw=False, vars=None):
        """Return a list of tuples with (name, value) for each option
        in the section.

        All % interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        `raw' is true.  Additional substitutions may be provided using the
        `vars' argument, which must be a dictionary whose contents overrides
        any pre-existing defaults.

        The section DEFAULT is special.
        """
        d = self._defaults.copy()
        try:
            d.update(self._sections[section])
        except KeyError:
            if section != DEFAULTSECT:
                raise NoSectionError(section)
        # Update with the entry specific variables
        if vars:
            for key, value in vars.items():
                d[self.optionxform(key)] = value
        options = d.keys()
        if "__name__" in options:
            options.remove("__name__")
        if raw:
            return [(option, d[option])
                    for option in options]
        else:
            return [(option, self._interpolate(section, option, d[option], d))
                    for option in options]

    def _interpolate(self, section, option, rawval, vars):
        # do the string interpolation
        value = rawval
        depth = MAX_INTERPOLATION_DEPTH
        while depth:                    # Loop through this until it's done
            depth -= 1
            if value and "%(" in value:
                value = self._KEYCRE.sub(self._interpolation_replace, value)
                try:
                    value = value % vars
                except KeyError as e:
                    raise InterpolationMissingOptionError(
                        option, section, rawval, e.args[0])
            else:
                break
        if value and "%(" in value:
            raise InterpolationDepthError(option, section, rawval)
        return value

    _KEYCRE = re.compile(r"%\(([^)]*)\)s|.")

    def _interpolation_replace(self, match):
        s = match.group(1)
        if s is None:
            return match.group()
        else:
            return "%%(%s)s" % self.optionxform(s)


class SafeConfigParser(ConfigParser):

    def _interpolate(self, section, option, rawval, vars):
        # do the string interpolation
        L = []
        self._interpolate_some(option, L, rawval, section, vars, 1)
        return ''.join(L)

    _interpvar_re = re.compile(r"%\(([^)]+)\)s")

    def _interpolate_some(self, option, accum, rest, section, map, depth):
        if depth > MAX_INTERPOLATION_DEPTH:
            raise InterpolationDepthError(option, section, rest)
        while rest:
            p = rest.find("%")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]
            if c == "%":
                accum.append("%")
                rest = rest[2:]
            elif c == "(":
                m = self._interpvar_re.match(rest)
                if m is None:
                    raise InterpolationSyntaxError(option, section,
                        "bad interpolation variable reference %r" % rest)
                var = self.optionxform(m.group(1))
                rest = rest[m.end():]
                try:
                    v = map[var]
                except KeyError:
                    raise InterpolationMissingOptionError(
                        option, section, rest, var)
                if "%" in v:
                    self._interpolate_some(option, accum, v,
                                           section, map, depth + 1)
                else:
                    accum.append(v)
            else:
                raise InterpolationSyntaxError(
                    option, section,
                    "'%%' must be followed by '%%' or '(', found: %r" % (rest,))

    def set(self, section, option, value=None):
        """Set an option.  Extend ConfigParser.set: check for string values."""
        # The only legal non-string value if we allow valueless
        # options is None, so we need to check if the value is a
        # string if:
        # - we do not allow valueless options, or
        # - we allow valueless options but the value is not None
        if self._optcre is self.OPTCRE or value:
            if not isinstance(value, basestring):
                raise TypeError("option values must be strings")
        if value is not None:
            # check for bad percent signs:
            # first, replace all "good" interpolations
            tmp_value = value.replace('%%', '')
            tmp_value = self._interpvar_re.sub('', tmp_value)
            # then, check if there's a lone percent sign left
            if '%' in tmp_value:
                raise ValueError("invalid interpolation syntax in %r at "
                                "position %d" % (value, tmp_value.find('%')))
        ConfigParser.set(self, section, option, value)

import ast
class STFParser(SafeConfigParser):
    """
    STFParser class is used to parse the CI customized INI file
    """
    def __init__(self, filenames):
        """
        Construct STFParser with filenames
        :param list filenames: a list of files
        :return: None
        :author: Gemfield
        """
        super(STFParser, self).__init__(allow_no_value=True)
        self.optionxform = str
        self.filenames = filenames
        self.read(filenames)

    def isIniFileWritable(self):
        if not isinstance(self.filenames, str):
            raise ValueError('Does not support this API when ini file name is not a single string(e.g. a list)')
        return os.access(self.filenames, os.W_OK)

    def childHeaders(self, section = None):
        """
        get sub sect of a section
        :param str section: the section name
        :return: a list of following headers of current section header
        :author: Gemfield
        """
        sub_sections=[]

        sec_prefix = ''
        if section is not None:
            sec_prefix = section + ':'

        for s in self.sections():
            if s.startswith(sec_prefix):
                s = s[len(sec_prefix):].split(':', 1)[0]
                if s not in sub_sections:
                    sub_sections.append(s)

        return sub_sections

    def subSections(self, section = None):
        """
        get sub sections of a section
        :param str section: the section name
        :return: a list of all sub sections of the section
        :author: Gemfield
        """
        sub_sections=[]

        sec_prefix = ''
        if section is not None:
            sec_prefix = section + ':'

        for s in self.sections():
            if s.startswith(sec_prefix) and s not in sub_sections:
                sub_sections.append(s)

        return sub_sections

    def _evalRawData(self, section, option):
        l = None
        try:
            l = ast.literal_eval(self.get(section, option))
        except Exception, e:
            print(str(e))
            l = None
        return l

    def getList(self, section, option):
        """
        get value of a option and convert the value to list
        :param str section: the section name
        :param str option: the option name
        :return: a list, None if the value is not list type
        :author: Gemfield
        """
        l = self._evalRawData(section, option)
        if l is None:
            return None
        if not isinstance(l,list):
            return None
        return l

    def _getSet(self, section, option):
        s = self._evalRawData(section, option)
        if s is None:
            return None
        if not isinstance(s,set):
            return None
        return s

    def getDict(self, section, option):
        """
        get value of a option and convert the value to dict
        :param str section: the section name
        :param str option: the option name
        :return: a dict, None if the value is not dict type
        :author: Gemfield
        """
        d = self._evalRawData(section, option)
        if d is None:
            return None
        if not isinstance(d,dict):
            return None
        return d

    def updateDynamic(self, section, option, value=None):
        """
        update value of a option in the dynamic section.
        Note: call flushDynamic() to store the changes back to the original ini file.
        :param str section: the section name, must be a dynamic subsection(format: <section_name>:Dynamic )
        :param str option: the option name
        :author: Gemfield
        """
        #section is '*:Dynamic'
        is_option_exist = False
        is_section_exist = False
        for index, i in enumerate(self._lines):
            if i.section != section:
                continue
            is_section_exist = True
            if i.key != option:
                continue

            is_option_exist = True
            mo = self._optcre.match(i.line)
            if mo is None:
                raise Exception("Invalid option on %s in section %s, illegal format: %s" % (option, section, i.line))

            optname, vi, optval = mo.group('option', 'vi', 'value')
            optname = self.optionxform(optname.rstrip())
            comment = ''
            if optval is not None:
                if vi in ('=', ':') and ';' in optval:
                    # ';' is a comment delimiter only if it follows a spacing character
                    pos = optval.find(';')
                    if pos != -1 and optval[pos - 1].isspace():
                        comment = ' %s'%optval[pos:]
            i.line = "%s = %s%s\n" %(optname, value, comment)

        if not is_section_exist:
            raise Exception('section [%s] does not exist in INI file' % section)

        if not is_option_exist:
            for index, i in enumerate(self._lines):
                if i.section != section:
                    continue

                if i.key != '__name__':
                    continue

                item_ins = IniItem("%s = %s\n" %(option, value))
                item_ins.key = option
                item_ins.section = section
                self._lines.insert(index + 1, item_ins)
                break

        self.set(section, option, value)

    def flushDynamic(self):
        """
        to store the changes (made by updateDynamic function) back to the original ini file.
        :author: Gemfield
        """
        if not isinstance(self.filenames, str):
            raise ValueError('Does not support this API when ini file name is not a single string(e.g. a list)')
        if not os.access(self.filenames, os.W_OK):
            raise ValueError('Does not support this API when ini file is not writeable')

        with open(self.filenames, 'wb') as file:
            file.writelines([i.line for i in self._lines])

    def directUpdateDynamic(self, section, option, value=None):
        """
        update value of a option in the Dynamic section and store the change back to the original ini file.
        :param str section: the section name, must be a dynamic subsection(format: <section_name>:Dynamic )
        :param str option: the option name
        :author: Gemfield
        """
        self.updateDynamic(section, option, value)
        self.flushDynamic()

    def dumpSectionToFile(self, section, filename, append=False):
        """
        dump all options in a specified section to a new file.
        Note: section header will not keep in the new file.
        :param str section: the section name
        :param str filename: the file to dump to
        :param Bool append: if true, the options are append to the existed file
        :author: Gemfield
        """
        mode = 'w+'
        if append:
            mode = 'a+'
        with open(filename, mode) as fp:
            for (key, value) in self._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    key = "=".join((key, str(value).replace('\n', '\n\t')))
                fp.write("%s\n" % (key))
            fp.write("\n")


    def dumpOptionToFile(self, section, option, filename, append=False):
        """
        dump an option in a specified section to a new file.
        Note: section header will not keep in the new file.
        :param str section: the section name
        :param str option: the option name
        :param str filename: the file to dump to
        :param Bool append: if true, the option are append to the existed file
        :author: Gemfield
        """
        mode = 'w+'
        if append:
            mode = 'a+'
        with open(filename, mode) as fp:
            fp.write("%s=%s\n" % (option, self.get(section,option)))
