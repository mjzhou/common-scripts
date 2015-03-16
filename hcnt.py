#!/usr/bin/env python 
# -*-coding:utf-8-*-
import sys,os,time,re
def daemonize(stdin='/dev/null',stdout= '/dev/null', stderr= 'dev/null'):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  #first parent out
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" %(e.errno, e.strerror))
        sys.exit(1)

    os.chdir("/")
    os.umask(0)
    os.setsid()
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s]n" %(e.errno,e.strerror))
        sys.exit(1)

    for f in sys.stdout, sys.stderr: f.flush()
    si = file(stdin, 'r')
    so = file(stdout,'a+')
    se = file(stderr,'a+',0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
def start():
    if os.path.exists('/tmp/hcntpid'):
        print "hcnt has already runing..."
    else:
        daemonize('/dev/null','/var/log/hcnt.log','/var/log/hcnterr.log')
        pid = str(os.getpid())
        file('/tmp/hcntpid','w+').write("%s\n" % pid)
        hostinfo()
def stop():
    pid = file('/tmp/hcntpid','r').read()
    os.remove('/tmp/hcntpid')
    os.kill(int(pid), SIGTERM)
def restart():
    stop()
    start()
def memory_stat():
    mem = {}
    f = open("/proc/meminfo")
    lines = f.readlines()
    f.close()
    for line in lines:
        if len(line) < 2: continue
        name = line.split(':')[0]
        var = line.split(':')[1].split()[0]
        mem[name] = long(var) * 1.0
    mem['MemUsed'] = mem['MemTotal'] - mem['MemFree'] - mem['Buffers'] - mem['Cached']
    return mem
def disk_stat():
    L=[]
    fd = open("/proc/diskstats", 'r')
    lines = fd.readlines()
    fd.close()
    for part in lines:
        rs = re.findall(r'.*sd[a-z][^0-9].*',part)
        if(len(rs)):
            h=rs[0].split()
            L.append(h)
    return L
def cpu_stat():
    cpu = []
    cpuinfo = {}
    f = open("/proc/cpuinfo")
    lines = f.readlines()
    f.close()
    for line in lines:
        if line == '\n':
            cpu.append(cpuinfo)
            cpuinfo = {}
        if len(line) < 2: continue
        name = line.split(':')[0].rstrip()
        var = line.split(':')[1]
        cpuinfo[name] = var
    return cpu
def read_cpu_usage():
    """Read the current system cpu usage from /proc/stat."""
    try:
        fd = open("/proc/stat", 'r')
        lines = fd.readlines()
    finally:
        if fd:
            fd.close()
    for line in lines:
        l = line.split()
        if len(l) < 5:
            continue
        if l[0].startswith('cpu'):
            return l
    return []
def cpu_usage():
    cpus = {}
    """ 
    get cpu avg used by percent 
    """
    cpustr=read_cpu_usage()
    if not cpustr:
        return 0
    #cpu usage=[(user_2 +sys_2+nice_2) - (user_1 + sys_1+nice_1)]/(total_2 - total_1)*100  
    usni1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])+long(cpustr[5])+long(cpustr[6])+long(cpustr[7])+long(cpustr[4])
    usn1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])
    us1=long(cpustr[1])+long(cpustr[2])
    sy1=long(cpustr[3])+long(cpustr[6])+long(cpustr[7])
    wa1=long(cpustr[5])
    id1=long(cpustr[4])
    #usni1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])+long(cpustr[4])  
    #disk
    Io = sorted(disk_stat(), key=lambda s : s[2])
    time.sleep(1)
    cpustr=read_cpu_usage()
    if not cpustr:
        return 0
    usni2=long(cpustr[1])+long(cpustr[2])+float(cpustr[3])+long(cpustr[5])+long(cpustr[6])+long(cpustr[7])+long(cpustr[4])
    usn2=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])
    us2=long(cpustr[1])+long(cpustr[2])
    sy2=long(cpustr[3])+long(cpustr[6])+long(cpustr[7])
    wa2=long(cpustr[5])
    id2=long(cpustr[4])
    cputime=usni2-usni1
    In = sorted(disk_stat(), key=lambda s : s[2])
    #disk
    cpus['per']=(usn2-usn1)*100/cputime
    cpus['us']=(us2-us1)*100/cputime
    cpus['sy']=(sy2-sy1)*100/cputime
    cpus['wa']=(wa2-wa1)*100/cputime
    cpus['id']=(id2-id1)*100/cputime
    cpus['deltams'] = 1000.0 * ((us2+sy2+wa2+id2) - (us1+sy1+wa1+id1)) / len(cpu_stat());
    #disk
    disk=''
    for io in Io:
        i = Io.index(io)
        rd_ios = int(In[i][3]) - int(io[3])
        wr_ios = int(In[i][7]) - int(io[7])
        n_ios = rd_ios + wr_ios
        rtick = int(In[i][6]) - int(io[6])
        wtick = int(In[i][10]) - int(io[10])
        tick = int(In[i][12]) - int(io[12])
        n_tick = rtick + wtick
        if(n_ios):
            wait = str(round(float(n_tick)/float(n_ios),2))
        else:
            wait = str('0.00')
        rds = str((int(In[i][5]) - int(io[5]))/2)
        wrs = str((int(In[i][9]) - int(io[9]))/2)
        util = str(round(tick*100*100.00/cpus['deltams'],2))
        if(float(util)>100.00):
            util=str('100.00')
        iostat=wait+'\t'+rds+'\t'+wrs+'\t'+util+'\t'
        disk = disk+iostat
    cpus['disk']=disk
    return cpus
def load_stat():
    loadavg = {}
    f = open("/proc/loadavg")
    con = f.read().split()
    f.close()
    loadavg['lavg_1']=con[0]
    loadavg['lavg_5']=con[1]
    loadavg['lavg_15']=con[2]
    loadavg['nr']=con[3]
    loadavg['last_pid']=con[4]
    return loadavg
def net_sum():
    sum = os.popen("/sbin/ifconfig eth0 |sed -n 8p").read().replace("\n", '')
    return sum
def net_stat():
    net={}
    var = net_sum()
    sum = var.split(':')
    rx1 = sum[1].split(' ')[0]
    tx1 = sum[2].split(' ')[0]
    #print sum
    time.sleep(1)
    var2 = net_sum()
    sum2 = var2.split(':')
    rx2 = sum2[1].split(' ')[0]
    tx2 = sum2[2].split(' ')[0]
    net['rxs'] = (long(rx2) - long(rx1))  #** 2 #kb/s
    net['txs'] = (long(tx2) - long(tx1))  #** 2 #kb/s
    return net
def insert(sql):
    conn = MySQLdb.Connect(user='test', passwd='test', db='mtp', host='192.168.136.90',charset='utf8')     
    cur=conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
def get_info():
    #ip = os.popen("/sbin/ifconfig $1|sed -n 2p|awk  '{ print $2 }'|awk -F : '{ print $2 }'").read().replace("\n", '')
    hostname = os.popen("hostname").read().replace("\n", '')
    now = str(int(time.time()))
    #cpu
    cpu = cpu_stat()
    cpus = cpu_usage()
    cpu_core = len(cpu)
    cpu_per =str(round(cpus['per'],2))
    cpu_us =str(round(cpus['us'],2))
    cpu_sy =str(round(cpus['sy'],2))
    cpu_wa =str(round(cpus['wa'],2))
    cpu_id =str(round(cpus['id'],2))
    cpu_disk = cpus['disk']
    #load
    lavg = load_stat()
    lavg_1 = lavg['lavg_1']
    #lavg_5 = lavg['lavg_5']
    #lavg_15 = lavg['lavg_15']
    lavg_per =str(round((float(lavg_1)/float(cpu_core)) * 100,2))
    #mem
    mem = memory_stat()
    MemUsed = mem['MemTotal'] - mem['MemFree'] - mem['Buffers'] - mem['Cached']
    mem_used=str(round(MemUsed,2))
    mem_total=str(round(mem['MemTotal'],2))
    mem_free=str(round(mem['MemFree'],2))
    mem_buffers=str(round(mem['Buffers'],2))
    mem_cached=str(round(mem['Cached'],2))
    #net
    net = net_stat()
    net_rxs = str(net['rxs'])
    net_txs = str(net['txs'])
    info = now+'\t'+cpu_us+'\t'+cpu_sy+'\t'+cpu_wa+'\t'+cpu_id+'\t'+cpu_per+'\t'+lavg_1+'\t'+lavg_per+'\t'+mem_total+'\t'+mem_used+'\t'+mem_free+'\t'+mem_buffers+'\t'+mem_cached+'\t'+net_rxs+'\t'+net_txs+'\t'+cpu_disk
    #print info
    with open('/opt/'+'hcnt-'+hostname, 'a') as f:
        f.write(info+'\n')
def daemonize(stdin='/dev/null',stdout= '/dev/null', stderr= 'dev/null'):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  #first parent out
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" %(e.errno, e.strerror))
        sys.exit(1)

    os.chdir("/")
    os.umask(0)
    os.setsid()
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) 
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s]n" %(e.errno,e.strerror))
        sys.exit(1)

    for f in sys.stdout, sys.stderr: f.flush()
    si = file(stdin, 'r')
    so = file(stdout,'a+')
    se = file(stderr,'a+',0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
def hostinfo():
    while True:
        #sys.stdout.write(time.ctime()+"\n") 
        sys.stdout.flush()
        get_info()
if __name__ == "__main__":
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            start()
        elif 'stop' == sys.argv[1]:
            stop()
        elif 'restart' == sys.argv[1]:
            restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
