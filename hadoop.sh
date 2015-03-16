#!/bin/bash
#!/bin/bash
# Program:
#    Get system infomation such as host type, host sn,cou ,mem ,disk,Then send to ganglia by gmetric.
# History
# 2014/09/02 yyzhou2@iflytek.com Second release
IP=`/sbin/ifconfig $1|sed -n 2p|awk  '{ print $2 }'|awk -F : '{ print $2 }'`
HOSTNAME=`hostname`
if  [  -d  /home/hadoop/hadoop_logs ];then
size=`du -s /home/hadoop/hadoop_logs | awk '{print int($1/1024)}'`
gmetric -n hadoop_log -v $size -t int32  -u 'Size/MB' -S $IP:$HOSTNAME
fi

if  [  -d  /home/hadoop/hadoop_run_env ];then
sizer=`du -s /home/hadoop/hadoop_run_env | awk '{print int($1/1024)}'`
gmetric -n hadoop_run -v $sizer -t int32  -u 'Size/MB' -S $IP:$HOSTNAME
fi

count=`/usr/jdk1.7.0_55/bin/jps |grep YarnChild| wc -l`
gmetric -n yarnchild  -v $count -t int32 -u "%"  -S $IP:$HOSTNAME


core=`grep -c 'model name' /proc/cpuinfo`
uptime=`uptime | awk {'print $(NF-2)'}`
load=${uptime:0:4}
percent=`awk 'BEGIN{printf "%.2f\n",('$load'/'$core')*100}'`
gmetric -n loadone_percent  -v $percent  -t float  -S $IP:$HOSTNAME

logic_core=`cat /proc/cpuinfo  | grep processor | wc -l`
uptime_rate=`cat /proc/uptime | awk '{printf "%.2f\n",$2/($1)*100}'`
rate=`echo "sclae=2; $uptime_rate/$logic_core" | bc`
gmetric -n free_rate  -v $rate  -t float  -S $IP:$HOSTNAME

/usr/sbin/dmidecode|grep -A16 "Memory Device" | grep Speed >/tmp/speed
/usr/sbin/dmidecode|grep -A16 "Memory Device" | grep Size >/tmp/size
size=`/usr/bin/paste /tmp/size  /tmp/speed | grep [0-9] | awk '{OFS=":";print $2$3,$5$6}' |sort -r|uniq -c|awk '{OFS="*";print $1,$2}'`
total=`cat /proc/meminfo | awk 'NR==1{printf "%dGB",$2/(1024*1024)}'`
info=`echo $size | sed "s/ /+/g"`
memory=${total}"="${info}
gmetric -n mem_info -v $memory  -t string  -S $IP:$HOSTNAME

disk_total=`cat /proc/partitions  | grep 'sd[a-z]$'| awk '{print $3}' |awk '{sum+=$1} END {printf "%.2fTB",sum/(1000000000)}'`
gmetric -n disk_total -v $disk_total  -t string  -S $IP:$HOSTNAME

host_type=`/usr/sbin/dmidecode|grep 'Product Name'| awk 'NR==1{print $3$4}'`
host_sn=`/usr/sbin/dmidecode|grep 'Serial Number'| awk 'NR==1{print $3}'`
host_info=${host_type}"-"${host_sn}
gmetric -n host_info -v $host_info  -t string  -S $IP:$HOSTNAME

disk_info=""
list=`cat /proc/partitions  | grep 'sd[a-z]$'| awk '{print $4}'`
for s in $list
do
disk_vendor=`/usr/sbin/smartctl -a /dev/$s| grep Vendor|awk '{print $2}'`
disk_info=$disk_info"\n"$disk_vendor
done
count=`echo -e  $disk_info | awk 'NR>1{print $1,$2}'|uniq -c|awk '{OFS="*";print $2,$1}'`
info=`echo $count | sed "s/ /+/g"`
gmetric -n disk_info -v $info  -t string  -S $IP:$HOSTNAME
 

cpu_type=`cat /proc/cpuinfo | grep name | cut -f2 -d: | uniq -c | awk '{print $5}'`
cpu_core=`cat /proc/cpuinfo | grep "cpu cores" | uniq | awk -F: '{print $2}'`
cpu_count=`cat /proc/cpuinfo | grep "physical id" | sort | uniq | wc -l`
cpu_processor=`cat /proc/cpuinfo | grep "processor" | wc -l`
cpu_info="${cpu_type}*${cpu_count}${cpu_core},${cpu_processor},${total}"
cpu_sum=`echo $cpu_info | sed "s/ /,/g"`
gmetric -n cpu_info -v $cpu_sum  -t string  -S $IP:$HOSTNAME
host_cpu=${host_type}"-"${cpu_sum}
gmetric -n sum_info -v $host_cpu  -t string  -S $IP:$HOSTNAME
#!/bin/bash
io=`python /opt/ganglia_io.py` 
gmetric -n sum_io -v $io -t int32  -u 'KB/s' -S $IP:$HOSTNAME
