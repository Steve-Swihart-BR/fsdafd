# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 21:32:10 2020

@author: Steve
from:
    https://github.com/evan54/mysimplegui/blob/master/mysimplegui.py
"""

  
import PySimpleGUI as sg
import re
import warnings
import pandas as pd


class ListboxWithSearch:

    def __init__(self, values, key='', select_mode='single',
                 size=(None, None), sort_fun=False, bind_return_key=False,
                 is_single_mode=True):
        if not is_single_mode:
            select_mode = 'extended'
            warnings.warn('Ev: is_single_mode is going to be deprecated use '
                          'select_mode instead', DeprecationWarning)
        g='hello'
        self._key = key
        self._sort = sort_fun if sort_fun else lambda x: list(x)
        self._input_key = key + '_input'
        self._select_all_key = key + '_select_all'
        self._deselect_all_key = key + '_deselect_all'
        self._clear_search_key = key + '_clear_search'
        self._values = values
        self._selected = set()
        self._displayed_secret = values
        self._el = sg.Listbox(values=self._sort(self._displayed),
                              size=self._initialise_size(size),
                              key=key,
                              select_mode=select_mode,
                              default_values=[g],
                              bind_return_key=bind_return_key, enable_events=True)
        self._i = sg.I(key=self._input_key, enable_events=True,
                       tooltip='''
Start a string with = and everything after will be considered a regexp
otherwise it will be a simple match:
eg enter:
    =.*world$
vs entering
    world''')
        buttons = []
        if select_mode != 'single':
            buttons.append(sg.B('Select all', key=self._select_all_key))
        buttons.append(sg.B('Deselect all', key=self._deselect_all_key))
        buttons.append(sg.B('Clear search', key=self._clear_search_key))
        self.layout = sg.Column([
            [self._i],
            buttons,
            [self._el]])

    def frame_layout(self, name):
        return sg.Frame(name, layout=[[self.layout]])

    def _initialise_size(self, size):
        size = list(size)
        if size[0] is None and len(self._values) > 0:
            size[0] = max(len(x) for x in self._values) + 1
        if size[1] is None and len(self._values) > 0:
            size[1] = len(self._values) + 1
        return size

    @property
    def _displayed(self):
        return self._displayed_secret

    @property
    def selected(self):
        return tuple(self._selected)

    @_displayed.setter
    def _displayed(self, values):
        self._displayed_secret = (values if isinstance(values, dict)
                                  else set(values))
        self._el.Update(values=self._sort(self._displayed_secret),
                        set_to_index=0)

    def update(self, values):

        original_displayed = tuple(self._displayed)
        is_regexp = not(len(values[self._input_key]) > 0 and
                        values[self._input_key][0] == '=')

        if not is_regexp:
            search_string = values[self._input_key][1:]
        else:
            search_string = '.*' + re.escape(values[self._input_key]) + '.*'
        selected = values[self._key]

        def match_fun(s):
            try:
                return re.match(search_string, s, re.I)
            except re.error:
                return True

        # update displayed
        if isinstance(self._values, dict):
            self._displayed = {s: y for s, y in self._values.items()
                               if match_fun(s)}
        else:
            self._displayed = [s for s in self._values if match_fun(s)]

        self._update_selection(selected, original_displayed)

    def _update_selection(self, selected, original_displayed):
        # update selection
        if self._el.SelectMode in ['multiple', 'extended']:
            self._selected = self._selected - set(original_displayed)
            self._selected.update(selected)
        elif self._el.SelectMode == 'single':
            if len(selected) > 0:
                self._selected = set(selected)
        else:
            raise ValueError(self._el.SelectMode,
                             'expected "single" or "multiple"')
        selected_and_displayed = self._selected.intersection(self._displayed)

        # self._el.Update(values=self._sort(self._displayed), set_to_index=0)
        self._el.SetValue(selected_and_displayed)

    def _select_all_displayed(self):

        self._selected.update(self._displayed)
        self._el.SetValue(self._sort(self._displayed))

    def _deselect_all_displayed(self):

        for el in self._displayed:
            self._selected.discard(el)

        self._el.SetValue([])

    def set_values(self, values, selected=None):
        self._values = values
        self._displayed = values
        if selected is None:
            self._selected = set()
            self._el.SetValue([])
        else:
            if isinstance(selected, str):
                selected = [selected]
            self._selected = set(selected)
            self._el.SetValue(self._sort(selected))

    def _clear_search(self, values):
        selected = values[self._key]
        original_displayed = tuple(self._displayed)
        self._update_selection(selected, original_displayed)
        self._i.Update(value='')
        self.update({self._input_key: '',
                     self._key: tuple(self._selected)})

    def manage_events(self, event, values):
        if event == self._select_all_key:
            self._select_all_displayed()
        elif event == self._deselect_all_key:
            self._deselect_all_displayed()
        elif event == self._input_key:
            self.update(values)
        elif event == self._clear_search_key:
            self._clear_search(values)
        elif event is None:
            pass
        else:
            selected = values[self._key]
            original_displayed = tuple(self._displayed)
            self._update_selection(selected, original_displayed)


def show_hidden_files_button(win):
    """
    To be used with layouts that include sg.FileBrowser, the purpose is to
    allow hidden files to not be shown. Inspired from:
        https://stackoverflow.com/a/54068050/1764089
        and
        https://github.com/PySimpleGUI/PySimpleGUI/issues/1830
    example usecase:
        import PySimpleGui as sg
        win = sg.Window('Test', layout=[[sg.FileBrowser('Load file'),
                                         sg.Button('ok')]])
        show_hidden_files_button(win)
        while True:
            event, values = win.Read()
            if event is None:
                win.Close()
                break
    """
    # set up TKroot
    win.Read(timeout=0)

    # from https://stackoverflow.com/a/54068050/1764089
    try:
        win.TKroot.tk.call('tk_getOpenFile', '-foobarbaz')
    except sg.tk.TclError:
        pass
    win.TKroot.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
    win.TKroot.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')


if __name__ == '__main__':

    values = ['hello', 'hello world', 'my world', 'your wold', 'god']
    listbox1 = ListboxWithSearch(values, 'mylistbox')
    layout = [ [listbox1.layout]
              ]
    win = sg.Window('test', layout=layout, resizable=True)
    while True:
        event, values = win.Read()
        print(event, values)
        if event is None:
            print('hi',values)
            break
        else:
            listbox1.manage_events(event, values)