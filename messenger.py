import socket
import hashlib
import time
import sys, ctypes
import random
import base64
import os
import threading
from msvcrt import getch
import subprocess


clients_list=list()
clients_data=dict()


def log(msg):
    open('beta_messenger_logs.txt','a+').write(msg+'\n')



def fetch(sock):
    message=''
    while len(message)<1 or len(temp)<1 :
        temp = sock.recv(1024)
        message += temp.decode('utf-8')
    return message


def encode(string,key):
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return base64.urlsafe_b64encode(encoded_string.encode("utf-8"))



def decode(string,key):
    string = base64.urlsafe_b64decode(string).decode("utf-8")
    decoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        decoded_c = chr(ord(string[i]) - ord(key_c) % 256)
        decoded_chars.append(decoded_c)
    decoded_string = "".join(decoded_chars)
    return decoded_string

def findkey(code):
    key = hashlib.sha1((str(code)+"catchmeiff").encode('utf-8')).hexdigest()
    return key


def getmasterkey():
    code = int(random.Random().random() * 100000)
    key = hashlib.sha1((str(code)+"catchmeiff").encode('utf-8')).hexdigest()
    return (key,code)
    

def join(host,nickname,password,port=25632):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host,port))
    sock.send(nickname.encode('utf-8'))
    time.sleep(0.1)
    sock.send(password.encode('utf-8'))
    while True:
        try:
            resp=sock.recv(1024).decode('utf-8')
            if resp=='REFUSED':
                print('joining refused from host')
                sys.exit()
            elif resp=='ACCEPTED':
                print('connected to host')
                break
        except AttributeError:
            pass
    key=findkey((sock.recv(1024)).decode('utf-8'))
    time.sleep(0.1)
    room = decode(fetch(sock),key)
    os.system('cls')
    print("Room name : "+room)
    threading._start_new_thread(recv_message_client,(host,key,nickname))
    while True:
        try:
            print()
            message=''
            char = getch()
            while char != b'\r':
                if char == b'\x08':
                    message = message[:-1]
                    print('>('+nickname+') '+message+" ",end='\r')
                    char = getch()
                else:
                    message += char.decode('utf-8')
                    print('>('+nickname+') '+message,end='\r')
                    char = getch()
            send_message(message,host,key,port=25633)
        except KeyboardInterrupt:
            if input('\nWant to quit?(Y/N)\t').lower()=='y':
                sys.exit()
            else:pass    





def host(room,password,port=25632):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('',port))
    while True:
        sock.listen()
        client , address = sock.accept()
        client_ip , client_port = address
        print(client_ip+" connected via port "+str(client_port))
        client_nickname=client.recv(1024).decode('utf-8')
        if client.recv(1024).decode('utf-8')!=password :
            client.send('REFUSED'.encode('utf-8'))
            log(time.ctime()+'\t:\t{} refused to connect via port {} and {} nickname'.format(client_ip,str(client_port),client_nickname))
            continue
        else:
            client.send('ACCEPTED'.encode('utf-8'))
            log(time.ctime()+'\t:\t{} accepted to connect via port {} and {} nickname'.format(client_ip,str(client_port),client_nickname))
        time.sleep(0.1)
        key , code = getmasterkey()
        client.send(str(code).encode('utf-8'))
        time.sleep(0.1)
        client.send(encode(room,key).encode('utf-8'))
        global clients_list,clients_data
        clients_list.append(client_ip)
        message_stack = list()
        clients_data[client_ip]=(key,client_nickname,message_stack)
        client.close()


        
def broadcast(message,sender,port=25634):
    global clients_list,clients_data
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in clients_list :
        key = clients_data[i][0]
        sock2.connect((i,port))
        sock2.send(encode(message,key).encode('utf-8'))
        time.sleep(0.05)
        sock2.send(encode(sender,key).encode('utf-8'))
        sock2.close()
        sys.exit()

def recv_message_client(host,key,self_nick,port=25634):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('',port))
    while True:
        sock.listen()
        server , address = sock.accept()
        if address[0]==host:
            message = decode(fetch(server),key)
            time.sleep(0.05)
            sender_nickname = decode(fetch(server),key)
            if sender_nickname != self_nick:
                print('>('+sender_nickname+') '+message)
                server.close()
            else:
                server.close()
                pass
        else:
            server.close()
            pass



def send_message(message,host,key,port=25633):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host,port))
    resp=fetch(sock)
    if decode(resp,key)!="SUCCESS":
        print('could not send message\ntry again')
        return
    sock.send((encode(message,key)).encode('utf-8'))
    sock.close()


def recv_message_server(port=25633):
    print('Listener Started')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('',port))
    while True:
        sock.listen()
        sender,sender_address = sock.accept()
        try:
            global clients_list,clients_data
            if (clients_list.index(sender_address[0])+1):
                sender.send("SUCCESS".encode('utf-8'))
                message = fetch(sender)
                message = decode(message,clients_data[sender_address[0]][0])
                threading._start_new_thread(addto_message_stack,(message,clients_data[sender_address[0]][1]))
                threading._start_new_thread(broadcast,(message,clients_data[sender_address[0]][1]))
                sender.close()
                pass
            else:
                sender.send('REFUSED'.encode('utf-8'))
                sender.close()
                log(time.ctime()+'\t:\t{} attempted to establish unathorized connection via port {}'.format(sender_address[0],str(sender_address[1])))
                pass
        except ValueError:
            sender.send('REFUSED'.encode('utf-8'))
            sender.close()
            log(time.ctime()+'\t:\t{} attempted to establish unathorized connection via port {}'.format(sender_address[0],str(sender_address[1])))
            pass




def addto_message_stack(message,nickname):
    global clients_data,clients_list
    for ip in clients_list:
        clients_data[ip][2].append([nickname,message])
			
			
			
			
def message_hub_client(host,nickname,key,port=25634):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    while True:
        time.sleep(random.random())
        sock.connect((host,port))
        sock.send(encode("Whats's up?",key).encode('utf-8'))
        time.sleep(0.05)
        message = fetch(sock)
        if decode(message,key)!="Nothing Bro":
            message=decode(message,key)
            for mess in message.split("<<this_thing_is_a_message_splitter>>"):
                sender_nickname = mess.split(">><<splitter>><<")[0]
                if sender_nickname != nickname:
                    mess = mess.split(">><<splitter>><<")[1]
                    print('>('+sender_nickname+') '+mess)
        sock.close()



def message_hub_buss(port=25634):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.bind(('',port))
    while True:
        sock.listen()
        client,add = sock.accept()
        threading._start_new_thread(message_hub_server,(client,add))
        continue

def message_hub_server(client,address):
    global clients_list,clients_data
    temp=str()
    try:
        if (clients_list.index(address[0])+1):
            if fetch(client)=="Whats's up?":
                if len(clients_data[address[0]][2])==0:
                    client.send(encode("Nothing Bro",clients_data[address[0]][0]).encode('utf-8'))
                else:
                    for message in clients_data[address[0]][2]:
                        temp +=message[0]+">><<splitter>><<"+message[1]+"<<this_thing_is_a_message_splitter>>"
                    clients_data[address[0]][2].clear()
                    client.send(encode(temp,clients_data[address[0]][0]).encode('utf-8'))
        client.close()
    except:
        client.close()





    
#ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)




if len(sys.argv)<2:
    prop = input('H for hosting or J for joining')
    if prop.lower()=='h':
        subprocess.call("netsh advfirewall firewall add rule name=BetaMessenger dir=in action=allow protocol=TCP localport=25633")
        subprocess.call("netsh advfirewall firewall add rule name=BetaMessenger dir=in action=allow protocol=TCP localport=25632")
        host(input('what is your room name?\t'),input('password?\t'))

    if prop.lower()=='j':
        subprocess.call("netsh advfirewall firewall add rule name=BetaMessenger dir=in action=allow protocol=TCP localport=25634")
        join(input('host ip?\t'),input('nickname?\t'),input('password?\t'))
        
elif sys.argv[1].lower()=='h':
    subprocess.call("netsh advfirewall firewall add rule name=BetaMessenger dir=in action=allow protocol=TCP localport=25633")
    subprocess.call("netsh advfirewall firewall add rule name=BetaMessenger dir=in action=allow protocol=TCP localport=25632")
    threading._start_new_thread(recv_message_server,())
    host(input('what is your room name?\t'),input('password?\t'))
elif sys.argv[1].lower()=='j':
    subprocess.call("netsh advfirewall firewall add rule name=BetaMessenger dir=in action=allow protocol=TCP localport=25634")
    join(input('host ip?\t'),input('nickname?\t'),input('password?\t'))
else:
    print('Invalid argument')
    sys.exit()



    
