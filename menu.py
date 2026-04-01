'''
Implement a text-based menu with options such as: list all stops, query 
journeys, show network summary, load networks, exit. 
'''
from Team_2.io_handler import *

class Menu:
    def __init__(self, header_text, menu_options):
        self.header_text = header_text
        self.menu_options = menu_options

    def viewing(self):
        while True:
            print('\n'+'='*50)
            print(self.header_text)
            for key, (text, func) in self.menu_options.items():
                print(key + ':' + text)
            
            curr_operation = input('Select operation:')

            if curr_operation in self.menu_options:
                text, func = self.menu_options[curr_operation]
                print('calling function:' + func.__name__)
                try:
                    return(func())
                except Exception as e:
                    print(f'Error executing function: {e}')
            else:
                print('Invalid option! Please re-enter your option.')

def place_holder_func():
    return 'placeholder func called'

def exit_program():
    print("Exiting... Bye!")
    return 'Q' # Signal to stop the main loop

#main: view menu, 
def main_menu():
    main_menu = Menu('Main Menu', 
                     {'1': ('Query journey', place_holder_func), 
                      '2': ('List all stops', place_holder_func), 
                      '3': ('Show network summary', place_holder_func), 
                      'Q': ('Exit', exit_program)}) 
    while (main_menu.viewing() != 'Q'):
        pass