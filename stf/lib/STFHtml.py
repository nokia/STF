import os
import sys
import datetime
from stf.stf_utils import *
from abc import abstractmethod

class LineItem(object):
    def __init__(self, line):
        self.line = line
        self.key = None

NO_KEY_ERROR = 'no key found in current html'
class STFHtml(object):
    def __init__(self, f):
        self.file = f
        try:
            with open(self.file, 'w') as f:
                f.write("TEST Write Privilege")
        except Exception, e:
            errorAndExit(str(e))

        self.content = []
        self.op = 'append'
        self.op_dict = {'append': '_appendFile', 'insert': '_insertFile', 'replace': '_replaceFile'}
        self.keyword = NO_KEY_ERROR
        self.indent_count = 0
        #indent by 4 withspace
        self.ws_indent = ''
        self.operation_dict = {'open': 'out4open', 'close': 'out4close', 'openclose': 'out4openclose', 'content': 'out4content', 'start': 'out4start', 'end': 'out4end'}

    def writeFile(self, content, key=None):
        #content
        item = LineItem(content)
        item.key = key

        if self.op not in self.op_dict:
            raise Exception('operation is not supported: %s' % self.op)

        getattr(self, self.op_dict[self.op])(item)

    def _replaceFile(self, item):
        table_index = 0
        # find the last key index in the list
        for index, l in enumerate(self.content):
            if l.key == self.keyword:
                table_index = index
                self.content[table_index].line = item.line

        if table_index == 0:
            raise Exception(self.keyword)

    def _insertFile(self, item):
        table_index = 0
        # find the last key index in the list
        for index, l in enumerate(self.content):
            if l.key == self.keyword:
                table_index = index + 1

        if table_index == 0:
            raise Exception(self.keyword)

        self.content.insert(table_index, item)

    def _appendFile(self, item):
        self.content.append(item)

    def close(self):
        with open(self.file, 'wb') as f:
           f.writelines([l.line for l in self.content])

    def _indent(self, is_reverse=False):
        self.indent_count += -4 if is_reverse else 4
        if self.indent_count < 0:
            raise Exception("html tag open and close not correctly.")

        self.ws_indent = ' ' * self.indent_count

    def out(self, operation, tag='', content='', key=None):
        self.ws_indent = ' ' * self.indent_count

        if operation not in self.operation_dict:
            raise Exception('operation is not supported: %s' % operation)

        getattr(self, self.operation_dict[operation])(tag, content, key)

    def out4open(self, tag, content, key):
        self.writeFile("%s<%s>" % (self.ws_indent, tag), key)
        self._indent()

    def out4close(self, tag, content, key):
        self._indent(True)
        self.writeFile("%s</%s>" % (self.ws_indent, tag), key)

    def out4openclose(self, tag, content, key):
        self.writeFile("%s<%s>%s</%s>" % (self.ws_indent, tag, content, tag), key)

    def out4content(self, tag, content, key):
        if not tag:
            raise Exception("Must provide the parameter tag when parameter operation is 'content'.")

        self.writeFile("%s%s" % (self.ws_indent, tag), key)

    def out4start(self, tag, content, key):
        self.writeFile("%s<%s>" % (self.ws_indent, tag), key)
        self._indent()

    def out4end(self, tag, content, key):
        self._indent(True)
        self.writeFile("%s</%s>" % (self.ws_indent, tag), key)
        if self.indent_count != 0:
            raise Exception("html tag end not correctly.")

    @abstractmethod
    def init(self):
        pass



class STFHtmlTable(STFHtml):
    def __init__(self, f, table_header_list):
        super(STFHtmlTable, self).__init__(f)
        self.table_header_list = table_header_list
        self.table_row_list = []

    def init(self):
        self.initHtml()

    def initHtml(self):
        self.out('start', 'html')
        #header part
        self.out('open', 'head')
        self._writeStyleInHtmlHeader()
        self.out('close', 'head')
        #body part
        self.out('open', 'body')
        self.initHtmlBody()
        self.out('close', 'body')
        self.out('end', 'html')


    def initHtmlBody(self):
        self.startAndEndBodyTitle()
        self.out('open', 'div data-role="main" class="ui-content"')
        self.startAndEndBodySearchBox()
        self.startAndEndTable()
        self.out('close', 'div')

    def startAndEndTable(self):
        self.out('open', 'table data-role="table"  class="ui-responsive ui-shadow" id="testtable" data-filter="true" data-input="#filter"')
        self.startAndEndTableHeader()
        self.out('close', 'table')

    def _searchIndexText(self):
        self.out('open', 'input id="filter" data-type="search" placeholder="STF: Search in %d cases..." ' % len(self.table_row_list), key='search')

    # search filter, in body part
    def startAndEndBodySearchBox(self):
        self.out('open', 'form')
        self._searchIndexText()
        self.out('close', 'input')
        self.out('close', 'form')

    def replaceCaseNumber(self):
        self.op = 'replace'
        self.keyword = 'search'
        self._searchIndexText()
        self.keyword = NO_KEY_ERROR
        self.op = 'append'

    # body title, on middle top
    def startAndEndBodyTitle(self):
        self.out('open', 'div data-role="header"')
        self.out('openclose', 'h3', '@ <font color="green"><b>%s</b></font>' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.out('close', 'div')

    def startAndEndTableHeader(self):
        self.out('open', 'thead')
        self.out('open', 'tr')
        for s in self.table_header_list:
            self.out('openclose', 'th', s)
        self.out('close', 'tr')
        self.out('close', 'thead', key='tablerow')

    # d is a dict, which key is defined in table_header_list
    def addTableRow(self, d):
        self.op = 'insert'
        self.keyword = 'tablerow'
        self.table_row_list.append(dict(d))

        self.out('open','tr', key='tablerow')
        for s in self.table_header_list:
            self.out('openclose', 'td', d[s], key='tablerow')
        self.out('close', 'tr', key='tablerow')
        self.op = 'append'
        self.keyword = NO_KEY_ERROR
        self.replaceCaseNumber()

    def addTableRowList(self, d_list):
        for d in d_list:
            self.addTableRow(d)

    @abstractmethod
    def _writeStyleInHtmlHeader(self):
        pass

    def _sortTable(self):
        pass



class STFHtmlTableSyle4CSF(STFHtmlTable):
    def __init__(self, f, table_header_list):
        super(STFHtmlTableSyle4CSF, self).__init__(f, table_header_list)

    # do sorting work
    def _sortTable(self):
        self.table_row_list.sort(key=lambda x:x['Time'],reverse=True)

    def _writeStyleInHtmlHeader(self):
        self.out('content', '<link rel="stylesheet" href="http://csfci.ih.lucent.com/~csfdev/csf/auto/CSFcommon/lib/jQuery/jquery.mobile-1.4.5.min.css">')
        self.out('content', '<script src="http://csfci.ih.lucent.com/~csfdev/csf/auto/CSFcommon/lib/jQuery/jquery-1.12.4.min.js"></script>')
        self.out('content', '<script src="http://csfci.ih.lucent.com/~csfdev/csf/auto/CSFcommon/lib/jQuery/jquery.mobile-1.4.5.min.js"></script>')

        self.out('open', 'style')
        self.out('content', 'td {')
        self.out('content', 'font-size:11px;')
        self.out('content', '}')
        self.out('content', 'th {')
        self.out('content', 'border-bottom: 1px solid #d6d6d6;')
        self.out('content', '}')
        self.out('content', 'tr:nth-child(even){')
        self.out('content', 'background:#e9e9e9;')
        self.out('content', '}')
        self.out('close', 'style')


if __name__ == '__main__':
    l = ['No.', 'File:Line', 'Description', 'Priority','Author','Time', 'Jira ID']
    html = STFHtmlTableSyle4CSF('/tmp/gemfield.html', l)
    html.init()
    row1 = {'No.': '1234', 'File:Line': 'gemfield.txt:12', 'Description': 'gemfield is testing', 'Priority': '5','Author': 'Gemfield','Time': '2014-3-2', 'Jira ID': 'CSFTST-5'}
    row2 = {'No.': '3333', 'File:Line': 'gemfield.log:12', 'Description': 'gemfield is sleeping', 'Priority': '1',
           'Author': 'SYSZUX', 'Time': '2017-05-14', 'Jira ID': 'CSFTST-15'}
    #write one table role
    html.addTableRow(row1)
    html.addTableRow(row2)
    #repeat writeTableRow ...
    html.close()



