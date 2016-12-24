from fnmatch import fnmatch
import os
from sys import exit
import html2text
import re
import urllib
import shutil
import logging
import sqlite3
from sys import stdout


logging.basicConfig(filename='error_log.log', filemode='a')


class BackupEvernote(object):

    def __init__(self, evernote_dir, db_dir='', output_dir=''):
        self.forbidden = ["?", "#", "/", "\\", "*", '"', "<", ">", "|", "%", " "]
        self.fb_w_trail = self.forbidden
        del self.fb_w_trail[2]
        self.evernote_dir = evernote_dir
        self.db_dir = db_dir
        self.output_dir = output_dir

    def _counter(self, ind, msg):
        stdout.write('\r' + '\t%s: %s' % (msg, ind))
        stdout.flush()

    def _exception(self, msg, file_path, e):
        logging.error(e)
        while True:
            inp = input('Cannot %s: %s\n'
                        'Error: %s\n'
                        'Skip & continue? y/n: ' % (msg, file_path, e))
            if inp == 'y':
                break
            else:
                exit(0)
        return

    def _multi_asterisk_fix(self, matchobj):
        return matchobj.group(0)[1:]

    def _get_pt(self, string):
        path = string.split('[')[1].split(']')[0]
        title = string.split('(')[1].split(')')[0]
        return path, title

    def _image_url_fix(self, matchobj):
        url = ''
        string = matchobj.group(0)

        # remove escape chars
        if '\n' in string:
            string = string.replace('\n', ' ')

        # this is a url
        if '![' not in string:
            url, _ = self._get_pt(string)
            return '%s' % url

        # image contains url
        url_pat = re.compile(r'.(\[.*\])\(.*\)\(.*\)$', re.MULTILINE)
        if re.match(url_pat, string):
            url = string.rpartition('(')[-1].strip(')')

        # image with or without url
        title, path = self._get_pt(string)
        path = '%s/%s/%s' % (self.output_dir, 'uncategorized', path)

        # todo: image path (remove random dash? -_) i.e t seal img
        path = self._remove_chars(path, self.fb_w_trail, trail=True)
        path += '?800'
        if not url:
            return '{{%s|%s}}' % (path, title)
        else:
            return '[[%s|{{%s|%s}}]]' % (url, path, title)

    def _remove_asterisks(self, matchobj):
        return re.sub(r'\**', '', matchobj.group(0))

    def _fix_spacing(self, matchobj):
        # todo: add wider bullet conversions i.e imac note
        string = matchobj.group(0)
        s_len = len(string) - 1
        if s_len <= 1:
            return string
        elif s_len == 2:
            return '*'
        elif s_len == 6:
            return '    *'
        elif s_len == 7:
            return '    *'
        elif s_len == 11:
            return '        *'
        else:
            return string

    def to_zim_syntax(self, content):
        """ Consider editing this func to fit the syntax of your chosen note taking software"""
        # headers
        # todo: remove heading chars / do not add heading if proceeded by image or url
        # todo: only ensure 1 h1 header (first), replace other h1's with h2
        new_c = content.replace('####', '=').('### ', '== ').replace('## ', '==== ').replace('# ', '====== ')

        # line separation?
        # todo: remake regex r'[#*_-]{3,}' not proceeded by words (\W) i.e jsand
        line_pat = re.compile(r'^\*[^\S\n]*\*[^\S\n]*\*\n', re.MULTILINE)
        new_c = re.sub(line_pat, ('-' * 80), new_c)

        # todo: regex to replace 3+ line breaks with 2

        # todo: regex for bold text, 2 * followed by words then 2 *

        # todo: replace \- at start of the line with bullet

        # fix bullet lists
        new_c = re.sub(r'\*[^\S\n]+?\*', self._multi_asterisk_fix, new_c)  # multiple asterisks on same line
        spaces = re.compile(r'^[^\S\n]*\*', re.MULTILINE)
        new_c = re.sub(spaces, self._fix_spacing, new_c)

        # fix urls and images
        new_c = re.sub(r'\*{2}(\[)|\)\*{2}', self._remove_asterisks, new_c)
        # new_c = re.sub(r'!*\[[^\]]*\]\([^\)]*\)', self._image_url_fix, new_c)
        new_c = re.sub(r'!*[\\\[]*\[[^\]]*[\\\]]*\([^\)]*[\]\)]*(\([^\)]*\))*', self._image_url_fix, new_c)

        return new_c

    def edit_file(self, full_path, filename, to_zim=False):
        text_maker = html2text.HTML2Text()

        with open(full_path, 'r') as f:
            html = f.read()
        content = ''
        if html:
            try:
                content = text_maker.handle(unicode(html, errors='ignore'))
                content = content.encode('ascii', 'ignore')
                content = content.split('\00')[0]   # remove null chars
                content = content.replace('\.', '.')    # remove escape chars
            except Exception as e:
                self._exception('convert content of note to markdown', full_path, e)
        else:
            content = ''

        if to_zim:
            content = self.to_zim_syntax(content)

        fn_path = self._rename_file(full_path, filename)
        with open(fn_path, 'w') as f:
            try:
                f.write(content.encode('ascii', 'ignore'))
            except Exception as e:
                self._exception('save note', fn_path, e)
        return

    def _remove_chars(self, stack_or_nb, folder_chars, trail=False):
        try:
            if not trail:
                stack_or_nb = stack_or_nb.replace('/', '&')
            for char in folder_chars:
                if char in stack_or_nb:
                    stack_or_nb = stack_or_nb.replace(char, '_')
        except Exception:
            raise
        finally:
            return stack_or_nb

    def _rename_file(self, full_path, filename, trail=False):
        filename = self._remove_chars(filename, self.forbidden, trail)
        renamed = filename.replace('.html', '.txt')
        old_filename = full_path.rpartition('/')[-1]
        return full_path.replace(old_filename, renamed)

    def nbooks_to_dirs(self):
        """ creates notebook & notebook stack folder structure containing all respective notes"""
        print "\nOrganizing notes by directory (based on notebooks & stacks)..."
        copied = []
        con = sqlite3.connect(self.db_dir)
        notebooks = con.execute("SELECT * FROM notebook_attr;").fetchall()

        folder_chars = self.forbidden
        del folder_chars[2]

        for ind, i in enumerate(notebooks):
            nb_id, notebook, stack = i[0], i[1], i[2]
            stack = self._remove_chars(stack, folder_chars)
            notebook = self._remove_chars(notebook, folder_chars)

            nb_notes = con.execute('SELECT * FROM note_attr WHERE note_attr.notebook_uid = %s;' % nb_id)
            notes_set = {i[1] for i in nb_notes}
            s_dir = ''

            if notebook and not stack:
                notebook_dir = self.output_dir + '/' + notebook
                if not os.path.isdir(notebook_dir):
                    os.mkdir(notebook_dir)
                s_dir = notebook_dir
            else:
                if stack:
                    stack_path = self.output_dir + '/' + stack
                    if not os.path.isdir(stack_path):
                        os.mkdir(stack_path)
                    s_dir = stack_path
                if notebook:
                    nb_in_stack = self.output_dir + '/%s/%s' % (stack, notebook)
                    if not os.path.isdir(nb_in_stack):
                        os.mkdir(nb_in_stack)
                    s_dir = nb_in_stack

            for p, d, files in os.walk(self.evernote_dir):
                for f in files:
                    fl = urllib.unquote(f)
                    fl_name = fl.rpartition('.')[0]
                    f_path = os.path.join(p, f)

                    if fl_name in notes_set:
                        copied.append(fl)
                        out_path = os.path.join(s_dir, f)
                        shutil.copy(f_path, out_path)
                        os.rename(out_path, os.path.join(s_dir, fl))
            self._counter(ind, 'notebooks/stacks exported')

        self.transfer_uncategorized(copied)
        return

    def transfer_uncategorized(self, copied):
        print "\nTransfering the rest of the files that do not belong to a notebook..."
        uncategorized = os.path.join(self.output_dir, 'uncategorized')
        os.mkdir(uncategorized)
        ind = 0
        for fl in os.listdir(self.evernote_dir):
            if fl not in copied:
                f_path = os.path.join(self.evernote_dir, fl)
                out_path = os.path.join(uncategorized, fl)
                try:
                    shutil.copy(f_path, out_path)
                except IOError:
                    shutil.copytree(f_path, out_path)
                finally:
                    ind += 1
                    self._counter(ind, 'copied files/dirs')

        # rename all files and folders within output folder
        for p, dirs, files in os.walk(self.output_dir):
            for d in dirs:
                new_d = self._remove_chars(d, self.forbidden)
                new_d = new_d.replace('.html', '.txt')
                os.rename(os.path.join(p, d), os.path.join(p, new_d))
        for p, dirs, files in os.walk(self.output_dir):
            for f in files:
                new_f = self._remove_chars(f, self.forbidden)
                new_f = new_f.replace('.html', '.txt')
                os.rename(os.path.join(p, f), os.path.join(p, new_f))
        return

    def to_markdown(self, zim_sintax=False):
        print "\nConverting note syntax..."
        c_dir = self.output_dir or self.evernote_dir
        ind = 0
        for p, d, files in os.walk(c_dir):
            for f in files:
                fl_path = os.path.join(p, f)
                if fnmatch(f, '*.txt'):
                    self.edit_file(fl_path, f, zim_sintax)
                    ind += 1
                    self._counter(ind, 'edited files')

    def backup(self, notebooks_to_dirs=True, to_markdown=False, zim_sintax=False):
        if notebooks_to_dirs:
            self.nbooks_to_dirs()
        if to_markdown or zim_sintax:
            self.to_markdown(zim_sintax)
        return


if __name__ == '__main__':
    notes_dir = '/media/truecrypt2'
    db_dir = '/home/unknown/evernote_backup/Databases/shawnx22.exb'
    output_dir = '/home/unknown/tmp_notes'
    # output_dir = '/home/evernote_backup/Notes'

    ev = BackupEvernote(notes_dir, db_dir, output_dir)
    ev.backup()
    ev.to_markdown(zim_sintax=True)