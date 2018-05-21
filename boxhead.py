import json
import time
import socket
import struct
import urllib.request
import datetime
import threading
import os
import ctypes
from xml.dom import minidom

class Chatlogger:
    def __init__(self, Username, Password, IP, Port):

        self.NullByte = struct.pack('B', 0)
        self.BufSize = 4096
        self.InLobby = False
        self.OnlineUsers = {}
        self.OnlineUserMap = {}
        self.Blacklist = [] # will ignore from specified users
                         
        self.NameToIP = {'Squaresville': '45.32.193.38:1031', 'Boxhead Blvd.': '45.33.118.156:1031', 'Amsterdam':  '139.162.151.57:1031'}

        self.IPToName = {'45.32.193.38:1031': 'Squaresville', '45.33.118.156:1031': 'Boxhead Blvd.', '139.162.151.57:1031': 'Amsterdam'}

        self.ServerIP = IP
        self.ServerPort = Port
        self.BotServer = self.IPToName[ '{}:{}'.format(self.ServerIP, self.ServerPort)]

        #socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9150)
        #socket.create_connection = socks.create_connection
        #socket.socket = socks.socksocket

        self.connectToServer(Username, Password, self.ServerIP, self.ServerPort)
  
    def sendPacket(self, Socket, PacketData, Receive = False):
        Packet = bytes(PacketData, 'utf-8')

        if Socket:
            Socket.send(Packet + self.NullByte)

            if Receive:
                return Socket.recv(self.BufSize).decode('utf-8')

    def startKeepAlive(self, TimerSeconds = 0.1):
        if hasattr(self, 'SocketConn'):
            KeepAliveTimer = threading.Timer(TimerSeconds, self.startKeepAlive)
            KeepAliveTimer.daemon = True
            KeepAliveTimer.start()

            url = 'http://api.urbandictionary.com/v0/define?term=shit'
            res = urllib.request.urlopen(url) 
            data = json.loads(res.read().decode('utf-8'))
            definition = data['list'][0]['definition']
            self.sendPacket(self.SocketConn, "91" + definition + "C")

    def connectionHandler(self):
        Buffer = b''

        while hasattr(self, 'SocketConn'):
            try:
                Buffer += self.SocketConn.recv(self.BufSize)
            except OSError:
                if hasattr(self, 'SocketConn'):
                    self.SocketConn.shutdown(socket.SHUT_RD)
                    self.SocketConn.close()

            if len(Buffer) == 0:
                print('Disconnected')
                break
            elif Buffer.endswith(self.NullByte):
                Receive = Buffer.split(self.NullByte)
                Buffer = b''

                for Data in Receive:
                    Data = Data.decode('utf-8')

                    if Data.startswith('U'):
                        UserID = Data[1:][:3]
                        Username = Data[4:][:20].replace('#', '')

                        self.parseUserData(Data)
                    elif Data.startswith('D'):
                        UserID = Data[1:][:3]
                        Username = self.OnlineUsers[UserID]

                        CurrentInfo = '{}:{};{}'.format(self.ServerIP, self.ServerPort, time.strftime('%m/%d/%Y at %H:%M (EST)'))

                        del self.OnlineUserMap[Username]
                        del self.OnlineUsers[UserID]
                    elif Data.startswith('0g') or Data.startswith('0j'):
                        print('{{Server}}: {}'.format(Data[2:]))
                    elif Data.startswith('093'):
                        print('Secondary login')
                        break
                    elif Data.startswith('0f') or Data.startswith('0e'):
                        Time, Reason = Data[2:].split(';')
                        print('This account has just been banned [Time: {} / Reason: {}]'.format(Time, Reason))
                    elif Data.startswith('0c'):
                        print(Data[2:])

    def connectToServer(self, Username, Password, ServerIP, ServerPort):
        try:
            self.SocketConn = socket.create_connection((ServerIP, ServerPort))
        except Exception as Error:
            print(Error)
            return

        Handshake = self.sendPacket(self.SocketConn, '08HxO9TdCC62Nwln1P', True).strip(self.NullByte.decode('utf-8'))

        if Handshake == '08':
            Credentials = '09{};{}'.format(Username, Password)
            RawData = self.sendPacket(self.SocketConn, Credentials, True).split(self.NullByte.decode('utf-8'))

            for Data in RawData:
                if Data.startswith('A'):
                    self.InLobby = True
                    self.BotID = Data[1:][:3]
                    self.BotUsername = Data[4:][:20].replace('#', '')

                    print('Bot Username: {} / Bot ID: {} / Located in {}'.format(self.BotUsername, self.BotID, self.BotServer))

                    EntryPackets = ['02Z900_', '03_']

                    for Packet in EntryPackets:
                        self.sendPacket(self.SocketConn, Packet)

                    self.startKeepAlive()
                    ConnectionThread = threading.Thread(target=self.connectionHandler)
                    ConnectionThread.start()
                    break
                elif Data == '09':
                    print('Incorrect password')
                    break
                elif Data == '091':
                    print('Currently banned')
                    break
        else:
            print('Server capacity check failed')

    def parseUserData(self, Packet, Password = None):
        StatsString = Packet.replace('\x00', '')
        UserID = StatsString[1:][:3]
        Type = StatsString[:1]

        if Type == 'U':
            if self.InLobby == True:
                Username = StatsString[4:][:20].replace('#', '')
                StatsString = StatsString[24:]

                self.OnlineUsers[UserID] = Username
                self.OnlineUserMap[Username] = UserID
            else:
                Username = StatsString[9:][:20].replace('#', '')

                self.OnlineUsers[UserID] = Username
                self.OnlineUserMap[Username] = UserID


if __name__ == '__main__': # rest in pieces
    Chatlogger('calcium130',  'lolok', '45.32.193.38', 1031)
