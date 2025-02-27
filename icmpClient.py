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
    data = struct.pack("d", perf_counter()) #KODY: Attempting to resolve 0.0ms pings. All 'time()' calls replaced with 'perf_counter()'
    
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
        timeReceived = perf_counter() #get time to calculate delay #KODY: Attempting to resolve 0.0ms pings. All 'time()' calls replaced with 'perf_counter()'

        icmpHeader = recPacket[20:28] #prunes header from bit 160-224 of the packet
        icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader) #Remove data from pruned header

        if icmpType != 0: #If not an echo reply
            print("Error: ICMP Type", icmpType, "Code", code)
            return -1 #failed packet return
        if icmpType == 0 and packetID == curID: #If echo reply and part of current socket
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent #Return round-trip time

    except TimeoutError:
        print("Ping timed out.")
        return -1 #failed packet return

def pingCycle(dest, timeout):
    myID = os.getpid() & 0xFFFF
    pingSocket = openSocket()
    sendPing(pingSocket, myID, dest)
    delay = receivePing(pingSocket, myID, timeout)

    pingSocket.close()
    return delay

# def ping(host, timeout=1):
    # dest = gethostbyname(host)  # Resolve hostname to IP
    # print("Pinging " + dest + " now:\n")
    # total = 0
    # totalPingCount = 0
    # failedPingCount = 0
    # minimun = 0
    # maximum = 0
    # #Ping loop ended with ctrl^c to escape. Also calculates out TTS statistics to display on exit
    # while True:
    #     try:
    #         delay = pingCycle(dest, timeout)
    #         totalPingCount += 1
    #         if delay  == -1:
    #             failedPingCount += 1
    #             continue
    #         delay = int(round((delay*1000), 3)) #convert delay to ms   #KODY: Kept getting 0ms pings when rounding before conversion. Decided to convert to ms and then round afterwards.
    #         if totalPingCount == 1: #initializing min and max to first packet delay
    #             minimun, maximum = delay, delay
    #         total += delay #adding to total for average
    #         if delay < minimun:
    #             minimun = delay
    #         if delay > maximum:
    #             maximum = delay
    #         print(f"{delay}ms TTS")
    #         sleep(1)
    #     except KeyboardInterrupt:
    #         print("\nPing stopped.")
    #         print(f"Ping success rate: {totalPingCount - failedPingCount}/{totalPingCount} = {100 - int(failedPingCount/totalPingCount * 100)}%")
    #         print("Approximate round trip times in milli-seconds:")
    #         print(f"Minimum = {minimun}ms, Maximum = {maximum}, Average = {int(total/totalPingCount)}")
    #         break
## May be a bit ambitious, but I opted to bring the entire ping functionality into main. Helps with error handling and endless loops

def main():
    try:
        destination = input("Enter an address to ping: ")
        dest = gethostbyname(destination)
    except Exception as e:
        print(f"Error resolving address '{destination}': {e}")
        return

    print(f"Pinging {dest} now:\n")
    total = 0
    totalPingCount = 0
    failedPingCount = 0
    minimum = None
    maximum = None

    try:
        # Allow user to specify a finite number of pings, e.g., 4 pings
        num_pings = int(input("Enter the number of pings: "))
        if (num_pings < 1):
            raise ValueError #Throw error if attempting to ping 0 or less times (except right below)
    except ValueError:
        print("Invalid input. Defaulting to 4 pings.")
        num_pings = 4

    for _ in range(num_pings):
        delay = pingCycle(dest, timeout=1)
       # print('\n') 
        #print(delay * 1000)
        totalPingCount += 1
        if delay == -1:
            failedPingCount += 1
        else:
            delay_ms = round((delay * 1000),3) # KODY: Same change I made in ping(). Convert first, round after.
            if minimum is None or delay_ms < minimum:
                minimum = delay_ms
            if maximum is None or delay_ms > maximum:
                maximum = delay_ms
            total += delay_ms
            print(f"{delay_ms}ms round-trip time")
        sleep(1)

    # Display summary statistics
    if totalPingCount - failedPingCount > 0:
        average = int(total / (totalPingCount - failedPingCount))
    else:
        average = 0

    print("\nPing statistics:")
    print(f"  Pings sent: {totalPingCount}")
    print(f"  Pings received: {totalPingCount - failedPingCount}")
    print(f"  Success rate: {100 - int((failedPingCount/totalPingCount) * 100)}%")
    print(f"  Minimum = {minimum}ms, Maximum = {maximum}ms, Average = {average}ms")

if __name__ == "__main__":
    main()
