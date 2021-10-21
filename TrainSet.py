import torch.utils.data as data
import numpy as np
import os
import torch
from PIL import Image
class TrainSet(data.Dataset):
    # def __init__(self,feat_path):
    #     self.features=list()
    #     self.supp=list()
    #     self.labels = list()
    #     for dir in os.listdir(feat_path):
    #         if dir[0]!='.':
    #             dir_absolute_path=feat_path+'/'+dir
    #             for f in os.listdir(dir_absolute_path):
    #                 features = np.zeros((6, 50, 500))
    #                 if f[0]=='n':
    #                     normal=Image.open(dir_absolute_path+'/'+f)
    #                     normal=np.array(normal)
    #                     features[3]=normal[:,:,0]
    #                     features[4]=normal[:,:,1]
    #                     features[5]=normal[:,:,2]
    #                 elif f[0]=='t':
    #                     tumor=Image.open(dir_absolute_path+'/'+f)
    #                     tumor=np.asarray(tumor)
    #                     features[0]=tumor[:,:,0]
    #                     features[1]=tumor[:,:,1]
    #                     features[2]=tumor[:,:,2]
    #                 elif f[0]=='s':
    #                     sup_feat=np.load(dir_absolute_path+'/'+f)
    #                     self.supp.append(sup_feat)
    #             self.features.append(features)
    #             self.labels.append(1)
    def __init__(self,ccs_feat_path):
        self.sup_features=list()
        self.features=list()
        self.labels = list()
        for p in ["bam_0.2", "bam_0.5", "bam_0.7"]:
            for c in range(1, 23, 1):
                if c==20:
                    continue
                current_feat_path = ccs_feat_path + '/' + p + '/chr' + str(c)
                germline_path=current_feat_path+'/germline'
                for f in os.listdir(germline_path):
                    if f[0] != '.':
                        absolute_path = germline_path + '/' + f
                        sub_feature=np.zeros((6, 50, 500))

                        for image in os.listdir(absolute_path):
                            if image[0]=='n':
                                normal=Image.open(absolute_path+'/'+image)
                                normal=np.array(normal)
                                sub_feature[3]=normal[:,:,0]
                                sub_feature[4]=normal[:,:,1]
                                sub_feature[5]=normal[:,:,2]
                            elif image[0]=='t':
                                tumor=Image.open(absolute_path+'/'+image)
                                tumor=np.array(tumor)
                                sub_feature[0]=tumor[:,:,0]
                                sub_feature[1]=tumor[:,:,1]
                                sub_feature[2]=tumor[:,:,2]
                            elif image[0]=='s':
                                sup_feat=np.load(absolute_path+'/'+image)
                                self.sup_features.append(sup_feat)
                        self.features.append(sub_feature)
                        self.labels.append(0)
                somatic_path=current_feat_path+'/somatic'
                for f in os.listdir(somatic_path):
                    if f[0] != '.':
                        absolute_path = somatic_path + '/' + f
                        sub_feature=np.zeros((6, 50, 500))
                        for image in os.listdir(absolute_path):
                            if image[0]=='n':
                                normal=Image.open(absolute_path+'/'+image)
                                normal=np.array(normal)
                                sub_feature[3]=normal[:,:,0]
                                sub_feature[4]=normal[:,:,1]
                                sub_feature[5]=normal[:,:,2]
                            elif image[0]=='t':
                                tumor=Image.open(absolute_path+'/'+image)
                                tumor=np.array(tumor)
                                sub_feature[0]=tumor[:,:,0]
                                sub_feature[1]=tumor[:,:,1]
                                sub_feature[2]=tumor[:,:,2]
                            elif image[0] == 's':
                                sup_feat = np.load(absolute_path+'/'+image)
                                self.sup_features.append(sup_feat)
                        self.features.append(sub_feature)
                        self.labels.append(1)
        # for p in ["bam_0.2", "bam_0.5", "bam_0.7"]:
        #     for c in range(1, 23, 1):
        #         if c==20:
        #             continue
        #         current_feat_path = clr_feat_path + '/' + p + '/chr' + str(c)
        #         germline_path=current_feat_path+'/germline'
        #         for f in os.listdir(germline_path):
        #             if f[0] != '.':
        #                 absolute_path = germline_path + '/' + f
        #                 sub_feature=np.zeros((6, 50, 500))
        #
        #                 for image in os.listdir(absolute_path):
        #                     if image[0]=='n':
        #                         normal=Image.open(absolute_path+'/'+image)
        #                         normal=np.array(normal)
        #                         sub_feature[3]=normal[:,:,0]
        #                         sub_feature[4]=normal[:,:,1]
        #                         sub_feature[5]=normal[:,:,2]
        #                     elif image[0]=='t':
        #                         tumor=Image.open(absolute_path+'/'+image)
        #                         tumor=np.array(tumor)
        #                         sub_feature[0]=tumor[:,:,0]
        #                         sub_feature[1]=tumor[:,:,1]
        #                         sub_feature[2]=tumor[:,:,2]
        #                     elif image[0]=='s':
        #                         sup_feat=np.load(absolute_path+'/'+image)
        #                         self.sup_features.append(sup_feat)
        #                 self.features.append(sub_feature)
        #                 self.labels.append(0)
        #         somatic_path=current_feat_path+'/somatic'
        #         for f in os.listdir(somatic_path):
        #             if f[0] != '.':
        #                 absolute_path = somatic_path + '/' + f
        #                 sub_feature=np.zeros((6, 50, 500))
        #                 for image in os.listdir(absolute_path):
        #                     if image[0]=='n':
        #                         normal=Image.open(absolute_path+'/'+image)
        #                         normal=np.array(normal)
        #                         sub_feature[3]=normal[:,:,0]
        #                         sub_feature[4]=normal[:,:,1]
        #                         sub_feature[5]=normal[:,:,2]
        #                     elif image[0]=='t':
        #                         tumor=Image.open(absolute_path+'/'+image)
        #                         tumor=np.array(tumor)
        #                         sub_feature[0]=tumor[:,:,0]
        #                         sub_feature[1]=tumor[:,:,1]
        #                         sub_feature[2]=tumor[:,:,2]
        #                     elif image[0] == 's':
        #                         sup_feat = np.load(absolute_path+'/'+image)
        #                         self.sup_features.append(sup_feat)
        #                 self.features.append(sub_feature)
        #                 self.labels.append(1)
    def __len__(self):
        return len(self.labels)



    def __getitem__(self, index):
        return torch.tensor(self.features[index],dtype=torch.float),torch.tensor(self.sup_features[index],dtype=torch.float),torch.tensor(self.labels[index],dtype=torch.long)
