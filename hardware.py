import subprocess,sys,os
def linux_cpudata():
    grains = {}
    cpuinfo = '/proc/cpuinfo'
    if os.path.isfile(cpuinfo):
        with open(cpuinfo, 'r') as _fp:
            for line in _fp:
                comps = line.split(':')
                if not len(comps) > 1:
                    continue
                key = comps[0].strip()
                val = comps[1].strip()
                if key == 'processor':
                    grains['logic'] = int(val) + 1
                elif key == 'model name':
                    model = val.replace('Intel(R) Xeon(R) CPU ','').split(' ')
                    while '' in model: model.remove('')
                    grains['type'] = model[0]
                elif key == 'physical id':
                    grains['physical']=int(val)+1
                elif key == 'cpu cores':
                    grains['cores']=int(val)
    res='%s*%s,%s,%s' % (grains['type'],grains['physical'],grains['cores'],grains['logic'])
    return res
def cmd_file(cmd,file):
    handle = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
    content = handle.stdout.read()
    with open(file, 'w') as fw:
        fw.write(content)
def ip():
    cmd = "/sbin/ifconfig | grep addr:192 | awk  '{ print $2 }'|awk -F : '{ print $2 }'"
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        res = fr.read().strip()
        return res
def _memsize(data):
    if data == 62:
        data = '64' 
    elif data == 125:
        data = '128' 
    return data
def _memdata():
    grains = {'mem_total': 0}
    meminfo = '/proc/meminfo'
    if os.path.isfile(meminfo):
        with open(meminfo, 'r') as ifile:
            for line in ifile:
                comps = line.rstrip('\n').split(':')
                if not len(comps) > 1:
                    continue
                if comps[0].strip() == 'MemTotal':
                    grains['mem_total'] = int(comps[1].split()[0]) / (1024*1024)
    res='%sGB' % (_memsize(grains['mem_total']))
    return res
def _mem_consist(data):
    mem_speed = []
    mem_size = []
    mem_ss= []
    for mem in data:
        if '\tSpeed'  in mem:
            if 'MHz' in mem:
                mem_speed.append(mem.split(':')[1].strip().replace(' ',''))
        elif '\tSize' in mem:
            if 'MB' in mem:
                size = mem.split(':')[1].strip().replace(' ','')
                mem_size.append(size)
    i=0
    for ms in mem_speed:
       if 'MHz' in mem_speed[i]:
           mem='%s-%s' % (mem_size[i],mem_speed[i])
           mem_ss.append(mem)
       i+=1
    m = {}
    for i in mem_ss:
        if mem_ss.count(i)>0:
            m[i] = mem_ss.count(i)
    fres=''
    for (k,v) in  m.items():
        fres += '%s*%d' % (k,v)+'+'
    res= fres[:-1]
    return res
def _memory():
    cmd = '/usr/sbin/dmidecode'
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        res = _mem_consist(fr)
        return res
def _product():
    cmd = '/usr/sbin/dmidecode  -s system-product-name'
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        for brand in fr:
            res='%s' % (brand.strip())
        return res
def _sn():
    cmd = '/usr/sbin/dmidecode  -s  system-serial-number'
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        for sn in fr:
            res='%s' % (sn.strip())
        return res
def _raid(str):
    if 'Primary-0, Secondary-0' in str:
        return 'Raid0'
    elif 'Primary-5, Secondary-0' in str:
        return 'Raid5'
    elif 'Primary-1, Secondary-0' in str:
        return 'Raid1'
    elif 'Primary-1, Secondary-3' in str:
        return 'Raid10'
def _disk_raid():
    cmd = '/opt/MegaRAID/MegaCli/MegaCli64 -LDInfo -Lall -aALL'
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        product = []
        for line in fr:
           if 'RAID Level' in line:
               product.append(_raid(line))
        p = {}
        for i in product:
            if product.count(i)>0:
                p[i] = product.count(i)
        fres=''
        for (k,v) in  p.items():
           fres += '%s*%d' % (k,v)+'+'
        res= fres[:-1]
        if len(res)==0:
            res = 'None'
        return res

def _disk_vendor():
    cmd = '/opt/MegaRAID/MegaCli/MegaCli64 -pdlist -aALL'
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        product = []
        for line in fr:
            if 'Inquiry Data' in line:
                val = line.split(':')[1].split(' ')
                while '' in val: val.remove('')
                if 'WD' in val[0]:
                   val[0]='WD'
                elif 'HGST' in val[0]:
                   val[0]='HGST'
                elif 'SEAGATE' in val[0]:
                   val[0]='ST'
                product.append(val[0])
        p = {}
        for i in product:
            if product.count(i)>0:
                p[i] = product.count(i)
        fres=''
        for (k,v) in  p.items():
            fres += '%s*%d' % (k,v)+'+'
        res= fres[:-1]
        if len(res)==0:
            res = 'None'
        return res
def _raid_info():
    type = 'None'
    size = 'None'
    cmd = '/opt/MegaRAID/MegaCli/MegaCli64 -AdpAllInfo -aALL'
    file = 'MegaSAS.log'
    cmd_file(cmd,file)
    with open(file, 'r') as fr:
        for line in fr:
            if 'Product' in line: 
                type = line.split(':')[1].strip()
            elif 'Memory Size' in line:
                size = line.split(':')[1].strip()
        res = '%s;%s' % (type,size)
        return res
def handle(name): 
	#handle = subprocess.Popen('hostname',stdout=subprocess.PIPE,shell=True)
	#res = handle.stdout.readlines()[0][:-4]
        #res=_disk_raid()
        res = '%s;%s;%s;%s;%s;%s;%s;%s;%s' % (ip(),linux_cpudata(),_memdata(),_memory(),_product(),_sn(),_disk_raid(),_disk_vendor(),_raid_info())
        return  res
if __name__=='__main__': 
        info = handle('') 
        print info
