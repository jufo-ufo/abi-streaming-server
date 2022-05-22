##!/bin/bash

R1=`cat /sys/class/net/$1/statistics/rx_bytes`
T1=`cat /sys/class/net/$1/statistics/tx_bytes`

echo "" >> log_1.txt
echo "date: CPU%, Mem%, Net_in(rx), Net_out(tx)" >> log_1.txt

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
	echo "${time}: ${CPU_usage}, ${Mem_per}, ${Net_in}, ${Net_out}" >> log_1.txt
	R1=$R2
	T1=$T2
	wait
done
