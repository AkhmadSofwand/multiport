#!/bin/bash
#wget https://github.com/${GitUser}/
GitUser="KhaiVpn767"
#IZIN SCRIPT
MYIP=$(curl -sS ipv4.icanhazip.com)
if [[ -f /usr/local/etc/xray/domain ]]; then
  domain="$(cat /usr/local/etc/xray/domain)"
elif [[ -f /etc/xray/domain ]]; then
  domain="$(cat /etc/xray/domain)"
else
  domain="${IP:-$(wget -qO- icanhazip.com 2>/dev/null || echo "")}"
fi
ISP=$(curl -s ipinfo.io/org | cut -d " " -f 2-10 )
CITY=$(curl -s ipinfo.io/city )
WKT=$(curl -s ipinfo.io/timezone )
IPVPS=$(curl -s ipinfo.io/ip )
cname=$( awk -F: '/model name/ {name=$2} END {print name}' /proc/cpuinfo )
cores=$( awk -F: '/model name/ {core++} END {print core}' /proc/cpuinfo )
freq=$( awk -F: ' /cpu MHz/ {freq=$2} END {print freq}' /proc/cpuinfo )
tram=$( free -m | awk 'NR==2 {print $2}' )
swap=$( free -m | awk 'NR==4 {print $2}' )
# TOTAL ACC CREATE VMESS WS
totalvm=$(grep -c -E "^### " "/usr/local/etc/xray/config.json" )
# TOTAL ACC CREATE  VLESS WS
totalvl=$(grep -c -E "^### " "/usr/local/etc/xray/vless.json")
# TOTAL ACC CREATE  VLESS TCP XTLS
totaltcp=$(grep -c -E "^### " "/usr/local/etc/xray/xtls.json")
# TOTAL ACC CREATE  TROJAN
totaltr=$(grep -c -E "^### " "/usr/local/etc/xray/trojanws.json")
# TOTAL ACC CREATE  TROJAN GO
totalgo=$(grep -c -E "^### " "/etc/trojan-go/akun.conf")
# TOTAL ACC CREATE OVPN SSH
total_ssh="$(awk -F: '$3 >= 1000 && $1 != "nobody" {print $1}' /etc/passwd | wc -l)"
red='\e[0;31m'
#Download/Upload today
dtoday="$(vnstat -i "$IFACE" | grep "today" | awk '{print $2" "substr ($3, 1, 1)}')"
utoday="$(vnstat -i "$IFACE" | grep "today" | awk '{print $5" "substr ($6, 1, 1)}')"
ttoday="$(vnstat -i "$IFACE" | grep "today" | awk '{print $8" "substr ($9, 1, 1)}')"
#Download/Upload yesterday
dyest="$(vnstat -i "$IFACE" | grep "yesterday" | awk '{print $2" "substr ($3, 1, 1)}')"
uyest="$(vnstat -i "$IFACE" | grep "yesterday" | awk '{print $5" "substr ($6, 1, 1)}')"
tyest="$(vnstat -i "$IFACE" | grep "yesterday" | awk '{print $8" "substr ($9, 1, 1)}')"
#Download/Upload current month
dmon="$(vnstat -i "$IFACE" -m | grep "`date +"%b '%y"`" | awk '{print $3" "substr ($4, 1, 1)}')"
umon="$(vnstat -i "$IFACE" -m | grep "`date +"%b '%y"`" | awk '{print $6" "substr ($7, 1, 1)}')"
tmon="$(vnstat -i "$IFACE" -m | grep "`date +"%b '%y"`" | awk '{print $9" "substr ($10, 1, 1)}')"
clear
# OS Uptime
uptime="$(uptime -p | cut -d " " -f 2-10)"
# USERNAME
rm -f /usr/bin/user
username=$( curl https://raw.githubusercontent.com/${GitUser}/allow/main/ipvps.conf | grep $MYIP | awk '{print $2}' )
echo "$username" > /usr/bin/user
# Order ID
rm -f /usr/bin/ver
user=$( curl https://raw.githubusercontent.com/${GitUser}/allow/main/ipvps.conf | grep $MYIP | awk '{print $3}' )
echo "$user" > /usr/bin/ver
# validity
rm -f /usr/bin/e
valid=$( curl https://raw.githubusercontent.com/${GitUser}/allow/main/ipvps.conf | grep $MYIP | awk '{print $4}' )
echo "$valid" > /usr/bin/e
# DETAIL ORDER
username=$(cat /usr/bin/user)
oid=$(cat /usr/bin/ver)
exp=$(cat /usr/bin/e)
clear

# STATUS EXPIRED ACTIVE
Green_font_prefix="\033[32m" && Red_font_prefix="\033[31m" && Green_background_prefix="\033[42;37m" && Red_background_prefix="\033[4$below" && Font_color_suffix="\033[0m"
Info="${Green_font_prefix}(Active)${Font_color_suffix}"
Error="${Green_font_prefix}${Font_color_suffix}${Red_font_prefix}[EXPIRED]${Font_color_suffix}"

today=`date -d "0 days" +"%Y-%m-%d"`
Exp1=$(curl https://raw.githubusercontent.com/${GitUser}/allow/main/ipvps.conf | grep $MYIP | awk '{print $4}')
if [[ $today < $Exp1 ]]; then
sts="${Info}"
else
sts="${Error}"
fi
clear
# CERTIFICATE STATUS
d1=$(date -d "$valid" +%s)
d2=$(date -d "$today" +%s)
certifacate=$(( (d1 - d2) / 86400 ))
# PROVIDED
creditt=$(cat /root/provided)
# BANNER COLOUR
banner_colour=$(cat /etc/banner)
# TEXT ON BOX COLOUR
box=$(cat /etc/box)
# LINE COLOUR
line=$(cat /etc/line)
# TEXT COLOUR ON TOP
text=$(cat /etc/text)
# TEXT COLOUR BELOW
below=$(cat /etc/below)
# BACKGROUND TEXT COLOUR
back_text=$(cat /etc/back)
# NUMBER COLOUR
number=$(cat /etc/number)
# BANNER
banner=$(cat /usr/bin/bannerku)
ascii=$(cat /usr/bin/test)
clear
echo -e "\e[$banner_colour"
figlet -f $ascii "$banner"

echo -e "\e[$text Ｐｒｅｍｉｕｍ Ｓｃｒｉｐｔ"
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e   " \e[$back_text                    \e[30m[\e[$box SERVER INFORMATION\e[30m ]\e[1m                  \e[m"
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e "  \e[$text Cpu Model            :$cname"
echo -e "  \e[$text Number Of Core       : $cores"
echo -e "  \e[$text Cpu Frequency        :$freq MHz"
echo -e "  \e[$text Total Amount Of Ram  : $tram MB"
echo -e "  \e[$text System Uptime        : $uptime"
echo -e "  \e[$text Ip Vps/Address       : $IPVPS"
echo -e "  \e[$text Domain Name          : $domain\e[0m"
echo -e "  \e[$text Version Name         : Multiport/Websocket"
echo -e "  \e[$text Certificate Status   : Lifetime"
echo -e "  \e[$text Provided By          : $creditt"
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e  "\e[0;33m Traffic\e[0m     \e[0;31mToday     Yesterday    Month   "
echo -e  "\e[0;33m Download\e[0m    $dtoday    $dyest     $dmon   \e[0m"
echo -e  "\e[0;33m Upload\e[0m      $utoday    $uyest     $umon   \e[0m"
echo -e  "\e[0;33m Total\e[0m     \033[0;36m  $ttoday    $tyest     $tmon  \e[0m "
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e  "  \e[$number Ssh/Ovpn    Vmess   Vless   VlessXtls   Trojan   Trojan-GO"
echo -e  " \e[$below     $total_ssh          $totalvm       $totalvl         $totaltcp          $totaltr          $totalgo"
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e   " \e[$back_text                        \e[30m[\e[$box MAIN MENU\e[30m ]\e[1m                       \e[m"
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e   "  \e[$number (•1)\e[m \e[$below XRAY VMESS & VLESS\e[m          \e[$number (•7)\e[m \e[$below MENU THEMES\e[m"
echo -e   "  \e[$number (•2)\e[m \e[$below TROJAN XRAY & GO\e[m            \e[$number (•8)\e[m \e[$below CLEAR LOG VPS\e[m"
echo -e   "  \e[$number (•3)\e[m \e[$below OPENSSH & OPENVPN\e[m           \e[$number (•9)\e[m \e[$below CHANGE PORT\e[m"
echo -e   "  \e[$number (•4)\e[m \e[$below PANEL SHADOWSOCKS\e[m           \e[$number (10)\e[m \e[$below CHECK RUNNING\e[m"
echo -e   "  \e[$number (•5)\e[m \e[$below DNS Changer\e[m                 \e[$number (11)\e[m \e[$below TRAFFIC XRAY\e[m"
echo -e   "  \e[$number (•6)\e[m \e[$below SYSTEM MENU\e[m                 \e[$number (12)\e[m \e[$below INFO ALL PORT\e[m"
echo -e   "  \e[$number (13)\e[m \e[$below WARP\e[m                     \e[$number (14)\e[m \e[$below INSTALL BOT\e[m"
echo -e   "  \e[$number (15)\e[m \e[$below SETTING BOT\e[m"

echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e   "  \e[$below 𝗩𝗲𝗿𝘀𝗶𝗼𝗻 :𝟮.𝟬"
echo -e   "  \e[$below 𝐒𝐜𝐫𝐢𝐩𝐓 𝐁𝐲 𝐊𝐡𝐚𝐢 𝐕 𝐏 𝐍"
echo -e   ""
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e   "             \e[$below ►  𝐓𝐇𝐈𝐒 𝐒𝐂𝐑𝐈𝐏𝐓 𝐈𝐒 𝐍𝐎𝐓 𝐅𝐎𝐑 𝐒𝐀𝐋𝐄  ◄"
echo -e   "             \e[$below ► 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 𝙁𝙤𝙧 𝙐𝙨𝙞𝙣𝙜 𝙏𝙝𝙞𝙨 𝙎𝙘𝙧𝙞𝙥𝙩 ◄"
echo -e   " \e[$line════════════════════════════════════════════════════════════\e[m"
echo -e   ""
echo -e   "  \e[$below [Ctrl + C] For exit from main menu\e[m"
echo -e   "\e[$below "
read -p   "   Select From Options [1-15 or x] :  " menu
echo -e   ""
case $menu in
1)
xraay
;;
2)
trojaan
;;
3)
ssh
;;
4)
ssssr
;;
5)
wget https://raw.githubusercontent.com/KhaiVpn767/multiport/main/dns.sh && chmod +x dns.sh && ./dns.sh
;;
6)
system
;;
7)
themes
;;
8)
clear-log
;;
9)
change-port
;;
10)
check-sc
;;
11)
trafficxray
;;
12)
info
;;
13)
clear
if command -v warp >/dev/null 2>&1; then
  warp
else
  echo "WARP module belum ada dalam repo ini."
  read -n 1 -s -r -p "Tekan apa-apa untuk kembali..."
  menu
fi
;;
14)
clear
if command -v fvpn-install >/dev/null 2>&1; then
  fvpn-install
elif [[ -x /opt/fvpn/install.sh ]]; then
  (cd /opt/fvpn && bash install.sh)
else
  echo "Bot belum dipasang. Jalankan option 14 dulu."
  read -n 1 -s -r -p "Tekan apa-apa untuk kembali..."
  menu
fi
;;
15)
clear
if command -v fvpn-panel >/dev/null 2>&1; then
  fvpn-panel
else
  echo "Bot belum dipasang / panel tak wujud."
  read -n 1 -s -r -p "Tekan apa-apa untuk kembali..."
  menu
fi
;;
x)
clear
exit
echo  -e "\e[1;31mPlease Type menu For More Option, Thank You\e[0m"
;;
*)
clear
echo  -e "\e[1;31mPlease enter an correct number\e[0m"
sleep 1
menu
;;
esac
