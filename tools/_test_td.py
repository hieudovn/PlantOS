import socket
s = socket.socket()
s.settimeout(3)
try:
    s.connect(("tdengine", 6041))
    print("OK - TDengine reachable on port 6041")
except Exception as e:
    print(f"FAIL - {e}")
s.close()

# Also test 6030 (native port)
s2 = socket.socket()
s2.settimeout(3)
try:
    s2.connect(("tdengine", 6030))
    print("OK - TDengine reachable on port 6030")
except Exception as e:
    print(f"FAIL port 6030 - {e}")
s2.close()
