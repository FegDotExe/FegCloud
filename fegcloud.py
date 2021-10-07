from json import load, dumps
import os
import telegram
import telegram.ext
import telebot
import logging
from time import sleep
from rich.console import Console
from rich.table import Table
from rich.box import SQUARE
from pynput import keyboard

current_path = os.path.dirname(os.path.abspath(__file__))+"/"
logging.basicConfig(filename=current_path+"latest.log",filemode='a',format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',datefmt='%H_%M_%S',level=logging.DEBUG)
console=Console()

def jread(file):
    with open(current_path+file+".json",encoding="utf-8") as fail:
        data=load(fail)
    return data
def jwrite(file,data):
    with open(current_path+file+".json","w") as fail:
        fail.write(dumps(data,indent=4))
        fail.close

settings_dict=jread("settings")
def update_settings_dict(modified_element,value):
    settings_dict[modified_element]=value
    jwrite("settings",settings_dict)

class KeyWaiter():
    """A class which waits for a keypress"""
    def __init__(self,allow_holding=True):
        """If allow_holding is enabled, the script does not wait for the key to be up"""
        self.was_down=False
        self.was_up=False
        self.allow_holding=allow_holding
        self.key=""
    def key_down(self,key):
        self.was_down=True
        self.key=str(key)
        if self.allow_holding:
            return False
    def key_up(self,key):
        if self.was_down:
            self.was_up=True
            return False
    def wait_for_key(self):
        with keyboard.Listener(on_press=self.key_down,on_release=self.key_up,supress=True) as listener:
            listener.join()
        sleep(settings_dict["input_wait_time"])
        return self.key

def get_input(input_string,valid_options_list,input_cursor=">",reprint_input_string=False,print_not_valid_message=True,not_valid_message="The given value is not valid"):
    """Prints input_string and waits for user to input a valid value; a value is valid if it is present in the valid_options_list; if a valid value is given, it is then returned as a string"""
    given_input="@@@@@"
    if not reprint_input_string:
        console.print(input_string,end="")
    while given_input not in valid_options_list:
        if reprint_input_string:
            console.print(input_string,end="")
        given_input=input(input_cursor)
        if print_not_valid_message and given_input not in valid_options_list:
            print(not_valid_message)
    return given_input

def create_settings_table(cursor):
    settings_table=Table(show_header=False,box=SQUARE)
    settings_table.add_column("Index",style="bold green")
    settings_table.add_column("Name")
    settings_table.add_column("Type")
    i=0
    for setting in settings_dict:
        if cursor==i:
            index_string="[black on white]"+str(i)+"[/black on white]"
        else:
            index_string=str(i)
        settings_table.add_row(index_string,setting,str(type(settings_dict[setting])))
        i+=1
    return settings_table

def change_setting(cursor):
    """Changes the setting at cursor"""
    element_name=[element for element in settings_dict][cursor]
    initial_string="You chose to edit the element [bold green]%s[/bold green]; its current value is '[magenta]%s[/magenta]'"%(element_name,str(settings_dict[element_name]))
    console.print(initial_string)
    if str(type(settings_dict[element_name]))=="<class 'str'>":
        console.print("The element you are modifying is a string. Enter its new value down here, or press enter to leave it as it is")
        new_value=input(">")
        if new_value!="":
            update_settings_dict(element_name,new_value)
    elif str(type(settings_dict[element_name]))=="<class 'list'>":
        mode="@@@@"
        while mode!="2":
            mode=get_input("The element you are modifying is a list.\n[bold green]0[/bold green]│append element\n[bold green]1[/bold green]│remove element\n[bold green]2[/bold green]│exit\n", ["0","1","2"], print_not_valid_message=False)
            if mode=="0":
                input_value=input("Enter the value of the element you whish to append or press enter\n>")
                if input_value!="":
                    this_list=settings_dict[element_name]
                    if input_value not in this_list:
                        this_list.append(input_value)
                    update_settings_dict(element_name,this_list)
            elif mode=="1":
                input_value=input("Enter the value of the element you whish to remove or press enter\n>")
                if input_value!="":
                    this_list=settings_dict[element_name]
                    try:
                        this_list.remove(input_value)
                        update_settings_dict(element_name,this_list)
                    except:
                        pass
            console.clear()
            console.print("The current value is [magenta]%s[/magenta]"%(str(settings_dict[element_name])))
    else:
        input("At the moment a variable of the type %s cannot be modified. Press enter to go back"%(str(type(settings_dict[element_name]))))
        #TODO: sooner or later, add float support
def change_settings():
    """Displays the settings table and allows user to navigate it"""
    cursor=0
    pressed_key=""
    while True:#Get key up/down and navigate settings
        console.clear()
        console.print(create_settings_table(cursor))
        console.print("arrow keys to move around; enter to confirm; esc to exit")
        pressed_key=KeyWaiter().wait_for_key()
        #input(pressed_key)#Needed to test keys
        i=len(settings_dict)
        if pressed_key=="'s'" or pressed_key=="Key.down":
            cursor+=1
        elif pressed_key=="'w'" or pressed_key=="Key.up":
            cursor-=1
        elif pressed_key=="Key.enter":
            input("")#Catches the enter
            console.clear()
            change_setting(cursor)
        elif pressed_key=="Key.esc":
            break
        if cursor>=i:
            cursor=0
        if cursor<0:
            cursor=i-1
    console.clear()

class RandomBot():
    def __init__(self):
        self.bottino=telebot.TeleBot(settings_dict["cloud_token"])
        @self.bottino.message_handler(commands=["start"])
        def start(message):
            #print(message)
            console.print("Got a start message from user [cyan]%i[/cyan] in chat [cyan]%i[/cyan]"%(message.from_user.id,message.chat.id))
            self.bottino.stop_polling()

    def start_polling(self):
        console.print("[green]Starting polling[/green]")
        self.bottino.polling()
        console.print("[green]Ended polling[/green]")

this_bot=RandomBot()
while True:
    console.clear()
    action_input=get_input("Which action would you like to perform?\n[bold green]0[/bold green]│start polling\n[bold green]1[/bold green]│change settings\n",["0","1"],print_not_valid_message=False)
    if action_input=="0":
        this_bot.start_polling()#Ok so it stops here while polling
        input("Press enter to continue using the program (terminal will be cleared)")
    elif action_input=="1":
        change_settings()