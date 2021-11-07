import os
if __name__ == '__main__':
    # command = "python main.py --tumor '/home/duan/Desktop/somaticSV/bam/CCS/0.7/somatic_bam_chr20/sim.srt.bam' --normal '/home/duan/Desktop/somaticSV/bam/CCS/0.7/germline_bam_chr20/sim.srt.bam' --ref '/home/duan/Data/ref/chr20.fa'  --wkdir ~/Desktop/test -t 4"
    command="python main.py --tumor '/home/duan/Desktop/somaticSV/bam/NA19239_NA19240_mixed/0.7/mixed.chr20.bam' --normal '/home/duan/Desktop/somaticSV/bam/NA19239_NA19240_mixed/0.7/NA19239.chr20.bam' --ref '/home/duan/Data/ref/chr20.fa' --model '/Users/duan/Desktop/model.output' --wkdir /Users/duan/Desktop/bam_0.5/chr20/germline --output ~/Desktop/output.bed -t 1"
    os.system(command)


