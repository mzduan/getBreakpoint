import re
def getKV(str):
    ret=dict()
    splits=re.split(';',str)
    for kv in splits:
        infos=re.split('=',kv)
        if len(infos)==2:
            key=re.split('=',kv)[0]
            value=re.split('=',kv)[1]
            ret[key]=value
    return ret
if __name__ == '__main__':


    tags=['0.2','0.4','0.5','0.6','0.7','0.8']

    for t in tags:

        tumor_vcf=open('/home/duan/Desktop/getBreakpoint/results/simulate_chr20_20~40_0.2~0.8/cutesv/cutesv_40_tumor_'+t+'.vcf','r')
        normal_vcf = open('/home/duan/Desktop/getBreakpoint/results/simulate_chr20_20~40_0.2~0.8/cutesv/cutesv_40_normal.vcf', 'r')

        somatic_vcf = open('/home/duan/Desktop/getBreakpoint/results/simulate_chr20_20~40_0.2~0.8/cutesv/cutesv_40_somatic_'+t+'.vcf', 'w')

        tumor_readlines=list()
        normal_readlines=list()

        while True:
            l=tumor_vcf.readline()
            if l:
                if l[0]!='#':
                    #不存储BND !!
                    infos = re.split('\s+', l)
                    if infos[2][7:10]=="BND":
                        continue
                    tumor_readlines.append(l)
            else:
                break

        while True:
            l=normal_vcf.readline()
            if l:
                if l[0] != '#':
                    infos = re.split('\s+', l)
                    if infos[2][7:10]=="BND":
                        continue
                    normal_readlines.append(l)
            else:
                break


        for i in tumor_readlines:
            i_infos=re.split('\s+',i)

            i_sv_type=i_infos[2][7:10]
            i_sv_start=int(i_infos[1])
            i_sups=i_infos[7]

            i_kv=getKV(i_sups)
            if 'SVLEN' in i_kv.keys():
                i_sv_len=abs(int(i_kv['SVLEN']))
                i_sv_end=i_sv_start+i_sv_len
            else:
                continue
            find_flag=False

            if i_sv_len<50:
                continue

            for j in normal_readlines:
                j_infos = re.split('\s+', j)

                j_sv_type = j_infos[2][7:10]
                j_sv_start = int(j_infos[1])
                j_sups = j_infos[7]
                j_kv = getKV(j_sups)
                if 'SVLEN' in j_kv.keys():
                    j_sv_len = abs(int(j_kv['SVLEN']))
                    j_sv_end=j_sv_start+j_sv_len
                    if j_sv_len<50:
                        continue
                else:
                    continue
                if i_sv_type==j_sv_type and abs(i_sv_start-j_sv_start)<=100 and abs(i_sv_end-j_sv_end) <=100:
                    find_flag=True

            if not find_flag:
                somatic_vcf.write(i)


        tumor_vcf.close()
        normal_vcf.close()
        somatic_vcf.close()
