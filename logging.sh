##!/bin/bash

if [ $# -eq 0 ]
then
 echo "Missing first Argument (network insterface), exiting"
 exit -1
fi

R1=`cat /sys/class/net/$1/statistics/rx_bytes`
T1=`cat /sys/class/net/$1/statistics/tx_bytes`
time=$(($(date +%s%N)/1000000))
f=`echo "log_${time}.csv"`

echo "" >> $f
echo "date, CPU%, Temp°, Mem%, Net_in(rx), Net_out(tx), clients, Server_in(rx), Server_out(tx)" >> $f

while true
do
	sleep 1&
	R2=`cat /sys/class/net/$1/statistics/rx_bytes`
	T2=`cat /sys/class/net/$1/statistics/tx_bytes`
	Net_in=`echo "scale=2;($R2-$R1)/1024" | bc`
	Net_out=`echo "scale=2;($T2-$T1)/1024" | bc`
	CPU_usage=`top -b -n1 | fgrep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}'`
	Mem_per=`free -m | awk 'NR==2{printf "%.2f", $3*100/$2}'`
	time=$(date "+%Y-%m-%d %H:%M:%S")
	temp=`sensors -j coretemp-isa-0000 | jq -r  '.["coretemp-isa-0000"] | .["Package id 0"] | .["temp1_input"]'`
	server_info=`python3 get_server_info.py`
	echo "${time}, ${CPU_usage}, ${temp}, ${Mem_per}, ${Net_in}, ${Net_out}, ${server_info}" >> $f
	R1=$R2
	T1=$T2
	wait
done
