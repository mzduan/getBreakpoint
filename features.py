from breakpoints import get_breakpoints
from merge import merge_same_read
from insertion import merge_insertion,left_aligned_insertion
from supplement import get_somatic_kmer
import pysam
import numpy as np
import reference
from PIL import Image
import os
import multiprocessing
from skimage import transform
def record_I(aln,I_pos):
    ref_pos=aln.reference_start
    for c in aln.cigartuples:
        if c[0]==0:
            ref_pos=ref_pos+c[1]
        elif c[0]==1:
            if ref_pos in I_pos:
                I_pos[ref_pos]=c[1] if c[1]>I_pos[ref_pos] else I_pos[ref_pos]
            else:
                I_pos[ref_pos]=c[1]
                # print(ref_pos,c[1])
        elif c[0]==2:
            ref_pos=ref_pos+c[1]

def has_long_ID(aln,start,end):
    q_pos=aln.query_alignment_start
    r_pos=aln.reference_start
    for c in aln.cigartuples:
        if c[0]==0:
            q_pos=q_pos+c[1]
            r_pos=r_pos+c[1]
        elif c[0]==1:
            if c[1]>=30:
                if r_pos>=start and r_pos<=end:
                    return True

            q_pos=q_pos+c[1]
        elif c[0]==2:
            if c[1]>=30:
                if r_pos>=start and r_pos<=end:
                    return True
                elif r_pos<=end and r_pos+c[1]>=start:
                    return True
            r_pos=r_pos+c[1]

    return False

def is_normal(aln):
    for c in aln.cigartuples:
        if c[0] == 1 or c[0] == 2:
            if c[1] >= 50:
                return False
        if c[0]==4 or c[0]==5:
            if c[1]>=50:
                return False
    return True


def get_support_reads(sv_type,chro,bk,bam_file,type,name2ref_pos,ref_dict):
    read_names = list()
    support_reads=list()
    start=bk[0]
    end=bk[0]+bk[1]
    if sv_type=="INS":
        end=start+1


    if type=="tumor":
        read_names=bk[2]
        for i in range(len(bk[2])):
            name = bk[2][i]
            ref_pos = bk[6][i]
            # print(name,ref_pos)
            name2ref_pos[name] = ref_pos

    else:
        cdel,cins,cinv,cdup=get_breakpoints(bam_file,1,chro=chro,start=start-50,end=end+50,ref_dict=ref_dict)
        if sv_type=="DEL":
            if chro in cdel.keys():
                for b in cdel[chro]:
                    # print(b)
                    # bk1=b[0]
                    # bk2=b[0]+b[1]
                    # if abs(start-bk1)<=20 and abs(end-bk2)<=20:
                    #     read_names.extend(b[2])
                    for i in range(len(b[2])):
                        read_sv_pos=b[5][i]
                        read_sv_len=b[6][i]
                        # print(read_sv_pos,read_sv_len)
                        if abs(start-read_sv_pos)<=20 and min(read_sv_len,bk[1])/max(read_sv_len,bk[1])>=0.9:
                            name=b[2][i]
                            read_names.append(name)
        elif sv_type=="INS":
            if chro in cins.keys():
                for b in cins[chro]:
                    #考虑candidate sv里每个read的比对情况，有可能support read被聚类到了unsupport sv里
                    for i in range(len(b[2])):
                        read_sv_pos=b[6][i]
                        read_sv_len=b[7][i]
                        if abs(start-read_sv_pos)<=20 and min(read_sv_len,bk[1])/max(read_sv_len,bk[1])>=0.9:
                            name=b[2][i]
                            read_names.append(name)
                            ref_pos=b[6][i]
                            name2ref_pos[name]=ref_pos

        elif sv_type=="INV":
            if chro in cinv.keys():
                for b in cinv[chro]:
                    for i in range(len(b[2])):
                        read_sv_start=b[5][i]
                        read_sv_end=b[6][i]
                        read_sv_len=read_sv_end-read_sv_start
                        if abs(start-read_sv_start)<=20 and abs(end-read_sv_end)<=20 and min(read_sv_len,bk[1])/max(read_sv_len,bk[1])>=0.9:
                            name=b[2][i]
                            read_names.append(name)
                    # bk1=b[0]
                    # bk2=b[0]+b[1]
                    # if abs(start-bk1)<=20 and abs(end-bk2)<=20:
                    #     read_names.extend(b[2])
        elif sv_type=="DUP":
            if chro in cdup.keys():
                for b in cdup[chro]:
                    for i in range(len(b[2])):
                        read_sv_start=b[5][i]
                        read_sv_end=b[6][i]
                        read_sv_len=read_sv_end-read_sv_start
                        if abs(start-read_sv_start)<=20 and abs(end-read_sv_end)<=20 and min(read_sv_len,bk[1])/max(read_sv_len,bk[1])>=0.9:
                            name=b[2][i]
                            read_names.append(name)
                    # bk1=b[0]
                    # bk2=b[0]+b[1]
                    # if abs(start-bk1)<=20 and abs(end-bk2)<=20:
                    #     read_names.extend(b[2])
    bam = pysam.AlignmentFile(bam_file, 'r')
    sv_region_reads = bam.fetch(contig=chro, start=start - 1000, end=end +1000)
    for aln in sv_region_reads:
        if aln.query_name in read_names:
            support_reads.append(aln)

    bam.close()
    #支持同一个insertion的reads,可能通过CIGAR判断，也可能通过SA判断，统一为通过CIGAR判断

    if sv_type=='INS':
        merged=merge_insertion(support_reads,bk)
        return merged
    return support_reads

def get_ref_reads(sv_type,chro,bk,bam_file,sv_reads):
    # print("go")
    start=bk[0]
    end=bk[0]+bk[1]
    # print(start - 300, end + 300)
    if sv_type=="INS":
        end=start+1

    ref_reads=list()
    bam=pysam.AlignmentFile(bam_file,'r')
    sv_region_reads = bam.fetch(contig=chro, start=start - 50, end=end +50)
    for aln in sv_region_reads:
        # 对于很大的变异，不一定存在正常的reads跨过两个断点，此时就认为normal数量为0,此时依赖字符串特征判别是否是true somatic sv
        # print(aln.query_name,aln.reference_start,start,aln.reference_end,end)
        if aln not in sv_reads and aln.reference_start < start - 50 and aln.reference_end > end + 50:

            #并且必须要求该reads在此区域没有变异信号
            if not has_long_ID(aln,start-300,end+300):
                # print(aln.query_name)
                ref_reads.append(aln)

    bam.close()
    return ref_reads

def get_revised_reference(sv_type,chro,bk,ref_dict,somatic_bam_file,germline_bam_file,output_dir,kmer_size):

#  bk的格式：
# DEL:   [[pos,len,[read_name_list],[read_start_list],[read_end_list],[ref_start_list],[len_list],mean_left_confu,mean_right_confu]
# INS:   [[pos,len,[read_name_list],insert_seq,[read_start_list],[read_end_list],[ref_start_list],[len_list],mean_left_confu,mean_right_confu]
# INV:   [[pos,len,[read_name_list],[read_start_list],[read_end_list],[ref_start_list],[ref_end_list],mean_left_confu,mean_right_confu]
# DUP:   [[pos,len,[read_name_list],[read_start_list],[read_end_list],[ref_start_list],[ref_end_list],mean_left_confu,mean_right_confu]

    bk1=bk[0]
    bk2=bk[0]+bk[1]
    if sv_type=="INS":
        bk2=bk1+1

    name2ref_pos=dict()
    #找出支持reference以及支持sv的alignments'
    somatic_support_reads=get_support_reads(sv_type,chro,bk,somatic_bam_file,"tumor",name2ref_pos,ref_dict)
    somatic_ref_reads=get_ref_reads(sv_type,chro,bk,somatic_bam_file,somatic_support_reads)
    germline_support_reads=get_support_reads(sv_type,chro,bk,germline_bam_file,"normal",name2ref_pos,ref_dict)
    germline_ref_reads=get_ref_reads(sv_type,chro,bk,germline_bam_file,germline_support_reads)

    #     print(aln.query_name)
    #计算一下字符串特征
    type_counts,medium,mean_region_counts,min_lnormal_kmer_radio,max_lnormal_kmer_radio,mean_rnormal_kmer_radio,\
        min_rnormal_kmer_radio,max_rnormal_kmer_radio,mean_rnormal_kmer_radio,mean_read_counts,mean_clus,max_clus=get_somatic_kmer(sv_type, somatic_support_reads,
                                                         somatic_bam_file,germline_bam_file, ref_dict, chro, bk,kmer_size)


    sup_features = np.array([type_counts, medium, mean_region_counts,min_lnormal_kmer_radio,max_lnormal_kmer_radio,mean_rnormal_kmer_radio,\
        min_rnormal_kmer_radio,max_rnormal_kmer_radio,mean_rnormal_kmer_radio,bk[-2],bk[-1],mean_read_counts, mean_clus, max_clus,len(somatic_support_reads),len(somatic_ref_reads),
                             len(germline_support_reads),len(germline_ref_reads)])

    sv_str = output_dir + '/' + chro +'_'+sv_type + '_' + str(bk[0]) + '_' + str(bk[1])+'_'+str(len(somatic_support_reads))
    os.mkdir(sv_str)
    np.save(sv_str + '/sup_feat', sup_features)
    # print(type_counts,medium,mean_region_counts,mean_read_counts,mean_clus,max_clus,bk[-2],bk[-1])
    #调整insertion位置，否则会导致reference 被多次添加gap
    if sv_type=='INS':
        if len(somatic_support_reads)!=0 or len(germline_support_reads)!=0:
            somatic_support_reads,germline_support_reads , left_insertion_pos = left_aligned_insertion(somatic_support_reads,germline_support_reads,bk,name2ref_pos)
            bk1=left_insertion_pos
            bk2=left_insertion_pos+1

    #记录在哪些地方后面有I，以及I的个数,包括 somatic 以及 germline

    I_pos={}
    region_start=999999999
    region_end=-1
    for aln in somatic_support_reads:
        region_start=region_start if region_start < aln.reference_start else aln.reference_start
        region_end=region_end if region_end > aln.reference_end else aln.reference_end
        record_I(aln, I_pos)
    for aln in somatic_ref_reads:
        region_start=region_start if region_start < aln.reference_start else aln.reference_start
        region_end=region_end if region_end > aln.reference_end else aln.reference_end
        record_I(aln, I_pos)
    for aln in germline_support_reads:
        region_start = region_start if region_start < aln.reference_start else aln.reference_start
        region_end = region_end if region_end > aln.reference_end else aln.reference_end
        record_I(aln, I_pos)
    for aln in germline_ref_reads:
        region_start=region_start if region_start < aln.reference_start else aln.reference_start
        region_end=region_end if region_end > aln.reference_end else aln.reference_end
        record_I(aln, I_pos)

    # print(region_start,region_end)
    if chro in ref_dict.keys():
        if region_start<region_end:
            region_reference_seq=ref_dict[chro][region_start:region_end]
        else:
            region_reference_seq=""
            raise Exception('Error reference seq')
    else:
        raise Exception('Error chrom')


    #开始注入gap
    I_pos=sorted(I_pos.items(), key=lambda item: item[0])

    revised_region_reference_seq=""
    forward_pos=0
    for i in range(len(I_pos)):
        # print(I_pos[i][0],I_pos[i][1])
        revised_region_reference_seq=revised_region_reference_seq+region_reference_seq[forward_pos:I_pos[i][0]-region_start]+I_pos[i][1]*'-'
        forward_pos=I_pos[i][0]-region_start
    revised_region_reference_seq=revised_region_reference_seq+region_reference_seq[forward_pos:]


    #将reference坐标与revised_referenced对应起来
    revised2ref={}
    current_ref_pos=region_start
    for i in range(len(revised_region_reference_seq)):
        # revised2ref[current_ref_pos]=i
        if revised_region_reference_seq[i]=='-':
            continue
        else:
            revised2ref[current_ref_pos] = i
            # print(current_ref_pos,i)
            current_ref_pos=current_ref_pos+1
    if current_ref_pos!=region_end:
        raise Exception('Error in coordinate transformation!')
    revised2ref[current_ref_pos]=len(revised_region_reference_seq)


    bk1_in_revised=revised2ref[bk1]
    bk2_in_revised=revised2ref[bk2]
    # print(bk1,bk2)
    # 考虑到bk1和bk2不一定是准确的跨过变异区间，需要向左右拓展20bp
    if bk1-20 in revised2ref.keys() and bk2+20 in revised2ref.keys():
        bk1_in_revised=revised2ref[bk1-20]
        bk2_in_revised=revised2ref[bk2+20]
    return (revised_region_reference_seq,revised2ref,region_start,region_end,bk1_in_revised,bk2_in_revised,somatic_support_reads,germline_support_reads,somatic_ref_reads,germline_ref_reads)

def get_revised_reads(sv_reads,ref_reads,revised_reference,revised_dict,bk1_in_revised,bk2_in_revised):

    left_extend_bk1=bk1_in_revised-300 if bk1_in_revised-300 >=0 else 0
    right_extend_bk2=bk2_in_revised+300


    bk_sv_region_reads=list()
    bk_sv_region_reads.extend(sv_reads)
    bk_sv_region_reads.extend(ref_reads)


    #返回值
    read_seq_list=list()
    read_direction_list=list()
    read_depth_list=list()
    read_name_list = list()
    # read_basequal_list=list()

    for i in range(3):
        # read_seq_list.append(revised_reference)
        read_seq_list.append(revised_reference[left_extend_bk1:right_extend_bk2])
    ref_direction=""
    ref_depth=""
    for i in revised_reference:
        if i!='-':
            ref_depth=ref_depth+'1'
            ref_direction=ref_direction+'p'
        else:
            ref_depth=ref_depth+'0'
            ref_direction=ref_direction+'0'

    for i in range(3):
        read_direction_list.append(ref_direction[left_extend_bk1:right_extend_bk2])
        read_depth_list.append(ref_depth[left_extend_bk1:right_extend_bk2])
        # read_basequal_list.append(ref_basequal)
    for aln in bk_sv_region_reads:
        read_name_list.append(aln.query_name)
        read_align_seq=len(revised_reference)*'-'
        read_align_seq=list(read_align_seq)
        if aln.is_reverse:
            direction='m'
        else:
            direction='p'
        aln_ref_pos=aln.reference_start
        aln_read_pos=aln.query_alignment_start

        #  将  cigartuples  转为  base_cigar
        base_cigar = ""
        for t in aln.cigartuples:
            if t[0] == 0:
                base_cigar += t[1] * 'M'
            elif t[0] == 1:
                base_cigar += t[1] * 'I'
            elif t[0] == 2:
                base_cigar += t[1] * 'D'
            elif t[0] == 4:
                base_cigar += t[1] * 'S'
            elif t[0] == 5:
                base_cigar += t[1] * 'H'
        insert_len=0
        for c in base_cigar:
            if c=='M':
                insert_len=0
                read_align_seq[revised_dict[aln_ref_pos]]=aln.query_sequence[aln_read_pos]
                aln_read_pos=aln_read_pos+1
                aln_ref_pos=aln_ref_pos+1
            elif c=='I':
                read_align_seq[revised_dict[aln_ref_pos-1]+insert_len+1]=aln.query_sequence[aln_read_pos]
                aln_read_pos=aln_read_pos+1
                insert_len=insert_len+1
            elif c=='D':
                insert_len = 0
                aln_ref_pos=aln_ref_pos+1
        #表示比对方向的通道 p表示比对到正链，m表示比对到负链
        read_align_seq=read_align_seq[left_extend_bk1:right_extend_bk2]

        read_direction_seq=len(read_align_seq)*'0'
        read_direction_seq=list(read_direction_seq)
        for i in range(len(read_align_seq)):
            if read_align_seq[i]!='-':
                read_direction_seq[i]=direction

        # 表示depth的通道 1或者0 merge后会变成2
        read_depth_seq=len(read_align_seq)*'0'
        read_depth_seq=list(read_depth_seq)
        for i in range(len(read_align_seq)):
            if read_align_seq[i]!='-':
                read_depth_seq[i]='1'



        read_align_seq=''.join(read_align_seq)
        read_direction_seq=''.join(read_direction_seq)
        read_depth_seq=''.join(read_depth_seq)

        read_seq_list.append(read_align_seq)
        read_direction_list.append(read_direction_seq)
        read_depth_list.append(read_depth_seq)
        # read_basequal_list.append(read_basequal)


    return (read_seq_list,read_direction_list,read_depth_list,read_name_list,len(sv_reads),len(ref_reads))


def transfer(s_seq_list,g_seq_list,s_direction_list,g_direction_list,s_depth_list,g_depth_list):
    base_to_color = {'A': 250, 'G': 180, 'T': 100, 'C': 30, 'p': 220, 'm': 110, '1': 110, '2': 220,'0':0,'-':0,'N':0,'R':0}

    s_row=len(s_seq_list)
    g_row=len(g_seq_list)
    column=len(s_seq_list[0])
    features=np.zeros((6,50,column),dtype=np.int16)
    for i in range(50):
        if i<s_row:
            for j in range(column):
                f0=s_seq_list[i][j]
                f2=s_direction_list[i][j]
                f4=s_depth_list[i][j]
                # f6=s_basequal_list[i][j]
                features[0][i][j] = base_to_color[f0] if f0 in base_to_color.keys() else 0
                features[2][i][j] = base_to_color[f2]  if f2 in base_to_color.keys() else 0
                features[4][i][j] = base_to_color[f4]  if f4 in base_to_color.keys() else 0
                # features[6][i][j] = int(f6)/40*250
        else:
            features[0][i] = np.zeros(column)
            features[2][i] = np.zeros(column)
            features[4][i] = np.zeros(column)
            # features[6][i] = np.zeros(column)

    for i in range(50):
        if i<g_row:
            for j in range(column):
                f1 = g_seq_list[i][j]
                f3 = g_direction_list[i][j]
                f5 = g_depth_list[i][j]
                # f7 = g_basequal_list[i][j]
                features[1][i][j] = base_to_color[f1] if f1 in base_to_color.keys() else 0
                features[3][i][j] = base_to_color[f3] if f3 in base_to_color.keys() else 0
                features[5][i][j] = base_to_color[f5] if f5 in base_to_color.keys() else 0
                # features[7][i][j] = int(f7)/40*250
        else:
            features[1][i] = np.zeros(column)
            features[3][i] = np.zeros(column)
            features[5][i] = np.zeros(column)
            # features[7][i] = np.zeros(column)


    return features

def generate_features(sv_type,chro,bk,ref_dict,somatic_bam_file,germline_bam_file,output_dir,kmer_size):

    print("Generate Features for\t",sv_type,'\t',bk[0],'\t',bk[1])
    try:
        #获取修正过的 reference
        revised_region_reference_seq, revised2ref, \
        region_start,region_end,bk1_in_revised, bk2_in_revised,\
        somatic_support_reads,germline_support_reads,\
        somatic_ref_reads,germline_ref_reads = get_revised_reference(sv_type,chro,bk,ref_dict,somatic_bam_file,germline_bam_file,output_dir,kmer_size)


        #获取somatic features
        somatic_seq_list,somatic_direction_list,\
        somatic_depth_list,\
        somatic_name_list,s_sv_support_reads,s_ref_support_reads=get_revised_reads(somatic_support_reads,
                                                                                   somatic_ref_reads,
                                                                                   revised_region_reference_seq,
                                                                                   revised2ref,bk1_in_revised,bk2_in_revised)

        somatic_seq_list,somatic_direction_list,\
        somatic_depth_list=merge_same_read(somatic_seq_list,somatic_direction_list,
                                                                 somatic_depth_list,
                                                                 somatic_name_list)


        #获取germline features
        germline_seq_list,germline_direction_list,\
        germline_depth_list,\
        germline_name_list,g_sv_support_reads,g_ref_support_reads= get_revised_reads(germline_support_reads,
                                                                                     germline_ref_reads,
                                                                                     revised_region_reference_seq,
                                                                                     revised2ref,bk1_in_revised,bk2_in_revised)


        germline_seq_list,germline_direction_list,\
        germline_depth_list= merge_same_read(germline_seq_list,germline_direction_list,
                                                                germline_depth_list,
                                                                germline_name_list)

        features=transfer(somatic_seq_list,germline_seq_list,
                          somatic_direction_list,germline_direction_list,
                          somatic_depth_list,germline_depth_list,)

        sv_str=output_dir + '/' + chro + '_' + sv_type + '_' + str(bk[0]) + '_' + str(bk[1])+'_'+str(len(somatic_support_reads))
        #画两张图，somatic一张germline一张，然后resize成一样的大小
        dim1=50
        dim2=bk2_in_revised-bk1_in_revised+600
        dim2=min(dim2,len(somatic_seq_list[0]))
        somatic_base_channel = features[0]
        somatic_dir_channel = features[2]
        somatic_dep_channel = features[4]
        somatic_img = Image.new("RGB", (dim2, dim1))  #宽、高
        for i in range(dim1):
            for j in range(dim2):
                rcolor=somatic_base_channel[i][j]
                gcolor=somatic_dir_channel[i][j]
                bcolor = somatic_dep_channel[i][j]
                somatic_img.putpixel((j,i),(rcolor,gcolor,bcolor))
                # somatic_img.putpixel((j, i), (0, gcolor,0))
        somatic_img=np.array(somatic_img)
        transformed=transform.resize(somatic_img,(50,500))
        transformed=transformed*255
        # transformed=transformed.astype(np.float64)
        transformed = transformed.astype(np.uint8)
        transformed=Image.fromarray(transformed)
        transformed.save(sv_str+'/tumor.png')
        # np.save(sv_str+'/tumor',transformed)


        germline_base_channel = features[1]
        germline_dir_channel = features[3]
        germline_dep_channel = features[5]
        germline_img = Image.new("RGB", (dim2, dim1))
        for i in range(dim1):
            for j in range(dim2):
                rcolor=germline_base_channel[i][j]
                gcolor=germline_dir_channel[i][j]
                bcolor = germline_dep_channel[i][j]
                germline_img.putpixel((j,i),(rcolor,gcolor,bcolor))
                # germline_img.putpixel((j, i), (0, gcolor,0))
        germline_img=np.array(germline_img)
        transformed=transform.resize(germline_img,(50,500))
        transformed=transformed*255
        # transformed=transformed.astype(np.float64)
        transformed = transformed.astype(np.uint8)
        transformed=Image.fromarray(transformed)
        # np.save(sv_str+'/normal',transformed)
        transformed.save(sv_str+'/normal.png')

    except Exception as exp:
        msg="Error in\t"+somatic_bam_file+"\t"+sv_type+"\t"+str(bk[0])+"\t"+str(bk[1])
        print(msg)
        print(exp)


def run(cdel,cins,cinv,cdup,ref_dict,tumor,normal,wkdir,thread_num,kmer_size):

    # DEL:   [[pos,len,[read_name_list],[read_start_list],[read_end_list],[ref_start_list],[len_list],mean_left_confu,mean_right_confu]
    # INS:   [[pos,len,[read_name_list],insert_seq,[read_start_list],[read_end_list],[ref_start_list],[len_list],mean_left_confu,mean_right_confu]
    # INV:   [[pos,len,[read_name_list],[read_start_list],[read_end_list],[ref_start_list],[ref_end_list],mean_left_confu,mean_right_confu]
    # DUP:   [[pos,len,[read_name_list],[read_start_list],[read_end_list],[ref_start_list],[ref_end_list],mean_left_confu,mean_right_confu]

    pool = multiprocessing.Pool(processes=int(thread_num))
    for key in cdel:
        chro=key
        for bk in cdel[chro]:
            pool.apply_async(generate_features,("DEL",chro,bk,ref_dict,tumor,normal,wkdir,kmer_size))
    for key in cins:
        chro=key
        for bk in cins[chro]:
            pool.apply_async(generate_features,("INS",chro,bk,ref_dict,tumor,normal,wkdir,kmer_size))
    for key in cinv:
        chro=key
        for bk in cinv[chro]:
            pool.apply_async(generate_features,("INV",chro,bk,ref_dict,tumor,normal,wkdir,kmer_size))
    for key in cdup:
        chro=key
        for bk in cdup[chro]:
            pool.apply_async(generate_features,("DUP",chro,bk,ref_dict,tumor,normal,wkdir,kmer_size))
    # # pool.shutdown()
    pool.close()
    pool.join()
