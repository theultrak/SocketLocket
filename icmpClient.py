from socket import *
from time import *
import struct
import os

def openSocket():
    try:
        icmp_socket = socket(AF_INET, SOCK_RAW, getprotobyname("icmp") ) #raw socket opening.
        #print("Socket Open")
        return icmp_socket #Returns socket so it may be used outside the function to close it
    #common error running code for the first time
    except PermissionError as e:
        print(f"Error: {e}. Run with admin access.")
        exit()
#Check sum calculation for error detection
def checkSum(data):
    #print("Check sum on data:", data)
    data = bytearray(data)
    sum = 0
    counter = (len(data) // 2) * 2

    for count in range(0, counter, 2):
        thisVal = data[count+1] * 256 + data[count]
        sum = sum + thisVal
        sum = sum & 0xffffffff

    if counter < len(data):
        sum = sum + data[-1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def packetConstruction(myID):
    #print("Constructing packet")
    packetCheckSum = 0
    header = struct.pack("bbHHh", 8, 0, packetCheckSum, myID, 1) #build packet with dummy checksum
    data = struct.pack("d", time())
    
    packetCheckSum = checkSum(header + data) #get checksum of dummy packet
    packetCheckSum = htons(packetCheckSum) #converted to network bit order
    
    header = struct.pack("bbHHh", 8, 0, packetCheckSum, myID, 1) #repack header with completed checksum
    packedPacket = header + data
    return packedPacket

#simple packet send function that creates the packet then sends it out
def sendPing(openSocket, curID, dest):
    packet = packetConstruction(curID)
    
    openSocket.sendto(packet, (dest, 1)) #Sending packet created to destination using the icmp protocol(1)

def receivePing(openSocket, curID, timeout):
    openSocket.settimeout(timeout) #Set timeout speed for socket
    #Receive data with timeout handling
    try:
        recPacket, addr = openSocket.recvfrom(1024) #waits for packet receival
        timeReceived = time() #get time to calculate delay

        icmpHeader = recPacket[20:28] #prunes header from bit 160-224 of the packet
        icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader) #Remove data from pruned header

        if icmpType != 0: #If not an echo reply
            print("Error: ICMP Type", icmpType, "Code", code)
            return -1 #error handling return
        if icmpType == 0 and packetID == curID: #If echo reply and part of current socket
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent #Return round-trip time

    except TimeoutError:
        print("Ping timed out.")
        return -1 #error handling return

def pingCycle(dest, timeout):
    myID = os.getpid() & 0xFFFF
    pingSocket = openSocket()
    sendPing(pingSocket, myID, dest)
    delay = receivePing(pingSocket, myID, timeout)

    pingSocket.close()
    return delay

def ping(host, timeout=1):
    dest = gethostbyname(host)  # Resolve hostname to IP
    print("Pinging " + dest + " now:\n")
    total = 0
    totalPingCount = 0
    failedPingCount = 0
    minimun = 0
    maximum = 0
    #Ping loop ended with ctrl^c to escape. Also calculates out TTS statistics to display on exit
    while True:
        try:

            delay = pingCycle(dest, timeout)
            totalPingCount += 1
            if delay  == -1:
                failedPingCount += 1
                continue
            delay = int(round(delay,3) * 1000)
            if totalPingCount == 1:
                minimun, maximum = delay, delay
            total += delay
            if delay < minimun:
                minimun = delay
            if delay > maximum:
                maximum = delay
            print(f"{delay}ms TTS")
            sleep(1)
        except KeyboardInterrupt:
            print("\nPing stopped.")
            print(f"Ping success rate: {totalPingCount - failedPingCount}/{totalPingCount} = {100 - int(failedPingCount/totalPingCount * 100)}%")
            print("Approximate round trip times in milli-seconds:")
            print(f"Minimum = {minimun}ms, Maximum = {maximum}, Average = {int(total/totalPingCount)}")
            break
#destination = str(input("Enter an address to ping: "))
destination = "10.255.255.1"
ping(destination)
