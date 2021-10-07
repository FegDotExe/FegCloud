from json import load
import os
import telegram
import telegram.ext
import telebot
import logging
import threading
from time import sleep
from rich.console import Console
from rich.table import Table
from rich.box import SQUARE
from rich.live import Live
import keyboard

current_path = os.path.dirname(os.path.abspath(__file__))+"/"
logging.basicConfig(filename=current_path+"latest.log",filemode='a',format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',datefmt='%H_%M_%S',level=logging.DEBUG)
console=Console()

def jread(file):
    with open(current_path+file+".json",encoding="utf-8") as fail:
        data=load(fail)
    return data

settings_dict=jread("settings")

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
def change_settings():
    """Displays the settings table and allows user to navigate it"""
    cursor=0
    pressed_key=""
    while True:#Get key up/down and navigate settings
        console.clear()
        console.print(create_settings_table(cursor))
        console.print("w/s to move around; enter to confirm")
        pressed_key=keyboard.read_key()
        sleep(0.1)
        i=len(settings_dict)
        if pressed_key=="s":
            cursor+=1
        elif pressed_key=="w":
            cursor-=1
        elif pressed_key=="enter":
            break
        if cursor>=i:
            cursor=0
        if cursor<0:
            cursor=i-1
    input("")#Used to remove all the collected input
    console.clear()
    print(cursor)

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