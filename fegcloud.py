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
from math import ceil, floor

current_path = os.path.dirname(os.path.abspath(__file__))+"/"
logging.basicConfig(filename=current_path+"latest.log",filemode='a',format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',datefmt='%H_%M_%S',level=logging.DEBUG)
console=Console()

TABLE_EMPTYNESS=6

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
class IndexHelper():
    """Cool and good class to help with the pretty not cool and good indexing of tables"""
    def __init__(self,dictionary):
        self.current_path=["root"]
        self.previous_path="root"
        self.dictionary=dictionary
    def get_current_content(self):
        """Get the content of the current path"""
        return self.get_dict_from_path(self.current_path)
    def get_dict_from_path(self,path_list_input):
        """Get the dictionary for the given path list"""
        path_list=path_list_input.copy()
        this_dict=self.dictionary
        while len(path_list)>0:
            if path_list[0] in this_dict:
                if this_dict[path_list[0]]["type"]=="folder":
                    this_dict=this_dict[path_list[0]]["content"]
            del[path_list[0]]
        return this_dict
    def get_element(self,index,path=[]):
        """Returns a tuple containing dict and name of the element at given index in given path"""
        if path==[]:
            path=self.current_path
        element_dict=self.get_dict_from_path(path)
        
        output_name=""
        output_dict={}
        i=0
        for element in element_dict:
            if i==index:
                output_dict=element_dict[element]
                output_name=element
            i+=1
        return output_name,output_dict
    
    def get_max_page(self,size_y,path=[]):
        """Gets how many pages can be in this dict; returns a dictionary which looks like this: {"max_pages":1.825,"floor":1,"ceil":2}"""
        output_dict={}
        
        if path==[]:
            path=self.current_path
        size_y-=6
        total_elements=self.get_items_in_dict(path)

        max_pages=total_elements/size_y
        output_dict["max_pages"]=max_pages

        output_dict["floor"]=floor(max_pages)
        output_dict["ceil"]=ceil(max_pages)

        return output_dict

    def get_items_in_dict(self,path=[]):
        """Gets amount of items in said path"""
        if path==[]:
            path=self.current_path
        current_dict=self.get_dict_from_path(path)
        i=0
        for element in current_dict:
            i+=1
        return i
    def get_items_in_page(self,size_y,page,path=[]):
        """Gets the amount of items in a page in a said path as an int; size_y must be with the 6, it should be the actual size of the terminal"""
        if path==[]:
            path=self.current_path
        pages_amount=self.get_max_page(size_y,path)
        if page<pages_amount["floor"]:
            return size_y-TABLE_EMPTYNESS
        else:
            return self.get_items_in_dict(path)-((size_y-TABLE_EMPTYNESS)*pages_amount["floor"])

    def get_page_extremis(self,size_y,page,path=[]):
        """Gets the minimum and maximum values of indexes in a certain page; they are both returned together"""
        if path==[]:
            path=self.current_path
        items_in_first=self.get_items_in_page(size_y,0,path)
        lowest=items_in_first*page
        if page!=self.get_max_page(size_y,path)["ceil"]-1:
            highest=(items_in_first*(page+1))-1
        else:
            highest=((self.get_items_in_page(size_y,page,path)-1)+lowest)
        return lowest,highest

class Cloud():
    def __init__(self):
        cloud_dict=jread("cloud")
        self.y_size=os.get_terminal_size()[1]
        self.index_helper=IndexHelper(cloud_dict)
        self.page=0#Sets the current selection page to 0
        self.cursor=0
        self.display_table()
    def create_table(self,data_dict={}):
        output_table=Table(box=SQUARE)
        output_table.add_column("Id",style="bold green")
        output_table.add_column("Name")
        i=0
        for element in data_dict:
            if (self.y_size-TABLE_EMPTYNESS)*self.page<=i<=((self.y_size-TABLE_EMPTYNESS)*(self.page+1))-1:
                if data_dict[element]["type"]=="folder":
                    element_name=element+"/"
                else:
                    element_name=element
                if i==self.cursor:
                    output_table.add_row("[black on white]"+str(i)+"[/black on white]",element_name)
                else:
                    output_table.add_row(str(i),element_name)
            i+=1
        return output_table

    def display_table(self):
        while True:
            console.clear()
            console.print(self.create_table(self.index_helper.get_current_content()))
            console.print("[white]%i/%i - %s - h for help[/white]"%(self.page+1,self.index_helper.get_max_page(self.y_size)["ceil"],str(self.index_helper.current_path).replace("[","").replace("]","").replace(", ",",").replace(",","/").replace("'","")))
            pressed_key=KeyWaiter().wait_for_key()
            if pressed_key=="Key.right":
                if self.page+1<=self.index_helper.get_max_page(self.y_size)["floor"]:
                    self.page+=1
                    self.cursor+=(self.y_size-TABLE_EMPTYNESS)
            elif pressed_key=="Key.left":
                if self.page-1>=0:
                    self.page-=1
                    self.cursor-=(self.y_size-TABLE_EMPTYNESS)
            elif pressed_key=="Key.down":
                self.cursor+=1
            elif pressed_key=="Key.up":
                self.cursor-=1
            elif pressed_key=="'u'":
                #Add upload logic
                pass
            elif pressed_key=="Key.enter":
                #TODO: in future this will be used to move things and stuff
                selected_element=self.index_helper.get_element(self.cursor)
                if selected_element[1]["type"]=="folder":
                    self.index_helper.current_path.append(selected_element[0])
            elif pressed_key=="Key.esc":
                self.index_helper.current_path=self.index_helper.current_path[:-1]
                if self.index_helper.current_path==[]:
                    break
            elif pressed_key=="'h'":#Help section
                console.clear()
                console.print("[bold cyan]up/down[/bold cyan]: Navigate through a page\n[bold cyan]left/right[/bold cyan]: Navigate through pages\nPress enter to go back to the chart")
                input("")
            else:
                input(pressed_key)
            
            #Set cursor back to where it is supposed to be
            if self.cursor>self.index_helper.get_page_extremis(self.y_size,self.page)[1]:
                    self.cursor=self.index_helper.get_page_extremis(self.y_size,self.page)[0]
            if self.cursor<self.index_helper.get_page_extremis(self.y_size,self.page)[0]:
                    self.cursor=self.index_helper.get_page_extremis(self.y_size,self.page)[1]

this_bot=RandomBot()
while True:
    console.clear()
    action_input=get_input("Which action would you like to perform?\n[bold green]0[/bold green]│start polling\n[bold green]1[/bold green]│change settings\n[bold green]2[/bold green]│use the drive\n",["0","1","2"],print_not_valid_message=False)
    if action_input=="0":
        this_bot.start_polling()#Ok so it stops here while polling
        input("Press enter to continue using the program (terminal will be cleared)")
    elif action_input=="1":
        change_settings()
    elif action_input=="2":
        cloud=Cloud()
