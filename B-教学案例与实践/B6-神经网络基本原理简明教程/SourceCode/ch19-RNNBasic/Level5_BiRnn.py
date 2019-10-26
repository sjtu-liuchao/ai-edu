# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

from matplotlib import pyplot as plt
import numpy as np
import os
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from MiniFramework.EnumDef_6_0 import *
from MiniFramework.ActivationLayer import *
from MiniFramework.ClassificationLayer import *
from MiniFramework.LossFunction_1_1 import *
from MiniFramework.TrainingHistory_3_0 import *
from MiniFramework.HyperParameters_4_3 import *
from MiniFramework.WeightsBias_2_1 import *
from ExtendedDataReader.NameDataReader import *

file = "../../data/ch19.name_language.txt"

def load_data():
    dr = NameDataReader()
    dr.ReadData(file)
    dr.GenerateValidationSet(1000)
    return dr

class timestep(object):
    def forward_f2e(self, x, U1, U2, V1, V2, W1, W2, prev_s1, isFirst):
        self.x = x
        self.U1 = U1
        self.U2 = U2
        self.V1 = V1
        self.V2 = V2
        self.W1 = W1
        self.W2 = W2

        if (isFirst):
            # 公式1
            self.h1 = np.dot(x, U1)
        else:
            # 公式5
            self.h1 = np.dot(x, U1) + np.dot(prev_s1, W1) 
        #endif
        # 公式2
        self.s1 = Tanh().forward(self.h1)

    def forward_e2f(self, next_s2, isFirst, isLast):
        # backward
        if (isLast):
            # 公式3
            self.h2 = np.dot(self.x, self.U2)
        else:
            # 公式6
            self.h2 = np.dot(self.x, self.U2) + np.dot(next_s2, self.W2)
        #endif
        # 公式4
        self.s2 = Tanh().forward(self.h2)

        if (isFirst or isLast):
            self.z = np.dot(self.s1, self.V1) + np.dot(self.s2, self.V2)
            self.a = Softmax().forward(self.z)

    def backward_e2f(self, y, prev_s1, next_dh1, isFirst, isLast):
        if (isLast or isFirst):
            self.dz = self.a - y
        else:
            self.dz = np.zeros_like(y)

        if (isLast):
            # 公式13
            self.dh1 = np.dot(self.dz, self.V1.T) * Tanh().backward(self.s1)
        else:
            # 公式17
            self.dh1 = (np.dot(self.dz, self.V1.T) + np.dot(next_dh1, self.W1.T)) * Tanh().backward(self.s1)
        # end if

        self.dV1 = np.dot(self.s1.T, self.dz)
        # 公式11
        self.dU1 = np.dot(self.x.T, self.dh1)
        
        if (isFirst):
            # 公式20
            self.dW1 = np.zeros_like(self.W1)
        else:
            # 公式21,22
            self.dW1 = np.dot(prev_s1.T, self.dh1)
        # end if


    def backward_f2e(self, y, next_s2, prev_dh2, isFirst, isLast):
        if (isFirst):
            self.dz = self.a - y
        else:
            self.dz = np.zeros_like(y)

        if (isFirst):
            # 公式15
            self.dh2 = np.dot(self.dz, self.V2.T) * Tanh().backward(self.s2)
        else:
            # 公式19
            self.dh2 = (np.dot(self.dz, self.V2.T) + np.dot(prev_dh2, self.W2.T)) * Tanh().backward(self.s2)
        #end if

        self.dV2 = np.dot(self.s2.T, self.dz)     
        self.dU2 = np.dot(self.x.T, self.dh2)      

        if (isLast):
            # 公式20
            self.dW2 = np.zeros_like(self.W2)
        else:
            # 公式21,22
            self.dW2 = np.dot(next_s2.T, self.dh2)
        # end if


class net(object):
    def __init__(self, hp, model_name):
        self.hp = hp
        self.model_name = model_name
        self.subfolder = os.getcwd() + "/" + self.__create_subfolder()
        print(self.subfolder)

        if (self.load_parameters(ParameterType.Init) == False):
            self.U1,_ = WeightsBias_2_1.InitialParameters(self.hp.num_input, self.hp.num_hidden1, InitialMethod.Normal)
            self.U2,_ = WeightsBias_2_1.InitialParameters(self.hp.num_input, self.hp.num_hidden2, InitialMethod.Normal)
            self.V1,_ = WeightsBias_2_1.InitialParameters(self.hp.num_hidden1, self.hp.num_output, InitialMethod.Normal)
            self.V2,_ = WeightsBias_2_1.InitialParameters(self.hp.num_hidden2, self.hp.num_output, InitialMethod.Normal)
            self.W1,_ = WeightsBias_2_1.InitialParameters(self.hp.num_hidden1, self.hp.num_hidden1, InitialMethod.Normal)
            self.W2,_ = WeightsBias_2_1.InitialParameters(self.hp.num_hidden2, self.hp.num_hidden2, InitialMethod.Normal)
            self.save_parameters(ParameterType.Init)
        #end if

        self.loss_fun = LossFunction_1_1(self.hp.net_type)
        self.loss_trace = TrainingHistory_3_0()
        self.ts_list = []
        for i in range(self.hp.num_step+1):
            ts = timestep()
            self.ts_list.append(ts)
        #end for

    def __create_subfolder(self):
        if self.model_name != None:
            path = self.model_name.strip()
            path = path.rstrip("/")
            isExists = os.path.exists(path)
            if not isExists:
                os.makedirs(path)
            return path

    def forward(self,X):
        self.x = X
        self.batch = self.x.shape[0]
        self.ts = self.x.shape[1]

        #front to end
        for i in range(0, self.ts):
            if (i == 0):
                self.ts_list[i].forward_f2e(
                    X[:,i], 
                    self.U1, self.U2, self.V1, self.V2, self.W1, self.W2, 
                    None, True)
            else:
                self.ts_list[i].forward_f2e(
                    X[:,i], 
                    self.U1, self.U2, self.V1, self.V2, self.W1, self.W2, 
                    self.ts_list[i-1].s1[0:self.batch], False)
        #endfor
        #end to front
        for i in range(self.ts-1, -1, -1):
            if (i == self.ts - 1):
                self.ts_list[i].forward_e2f(None, False, True)
            elif (i == 0):
                self.ts_list[i].forward_e2f(self.ts_list[i+1].s2[0:self.batch], True, False)
            else:
                self.ts_list[i].forward_e2f(self.ts_list[i+1].s2[0:self.batch], False, False)
        #end for
        return self.ts_list[self.ts-1].a

    def backward(self,Y):
        #e2f
        for i in range(self.ts-1, -1, -1):
            if (i == self.ts - 1):
                self.ts_list[i].backward_e2f(
                    Y, 
                    self.ts_list[i-1].s1[0:self.batch], 
                    None, 
                    False, True)
            elif (i == 0):
                self.ts_list[i].backward_e2f(
                    Y, 
                    None,
                    self.ts_list[i+1].dh1[0:self.batch],
                    True, False)
            else:
                self.ts_list[i].backward_e2f(
                    Y, 
                    self.ts_list[i-1].s1[0:self.batch],
                    self.ts_list[i+1].dh1[0:self.batch],
                    False, False)
        #end for
        #fron to end
        for i in range(0, self.ts):
            if (i == 0):
                self.ts_list[i].backward_f2e(
                    Y, 
                    self.ts_list[i+1].s2[0:self.batch],
                    None,
                    True, False)
            elif (i == self.ts - 1):
                self.ts_list[i].backward_f2e(
                    Y, 
                    None,
                    self.ts_list[i-1].dh2[0:self.batch], 
                    False, True)
            else:
                self.ts_list[i].backward_f2e(
                    Y, 
                    self.ts_list[i+1].s2[0:self.batch],
                    self.ts_list[i-1].dh2[0:self.batch],
                    False, False)
        #end for

    def update(self):
        du1 = np.zeros_like(self.U1)
        du2 = np.zeros_like(self.U2)
        dv1 = np.zeros_like(self.V1)
        dv2 = np.zeros_like(self.V2)
        dw1 = np.zeros_like(self.W1)
        dw2 = np.zeros_like(self.W2)
        for i in range(self.ts):
            du1 += self.ts_list[i].dU1
            du2 += self.ts_list[i].dU2
            dv1 += self.ts_list[i].dV1
            dv2 += self.ts_list[i].dV2
            dw1 += self.ts_list[i].dW1
            dw2 += self.ts_list[i].dW2
        #end for
        self.U1 = self.U1 - du1 * self.hp.eta
        self.U2 = self.U2 - du2 * self.hp.eta
        self.V1 = self.V1 - dv1 * self.hp.eta
        self.V2 = self.V2 - dv2 * self.hp.eta
        self.W1 = self.W1 - dw1 * self.hp.eta
        self.W2 = self.W2 - dw2 * self.hp.eta

    def save_parameters(self, para_type):
        if (para_type == ParameterType.Init):
            print("save init parameters...")
            self.file_name = str.format("{0}/init.npz", self.subfolder)
        elif (para_type == ParameterType.Best):
            print("save best parameters...")
            self.file_name = str.format("{0}/best.npz", self.subfolder)
        elif (para_type == ParameterType.Last):
            print("save last parameters...")
            self.file_name = str.format("{0}/last.npz", self.subfolder)
        #endif
        np.savez(self.file_name, U1=self.U1, U2=self.U2, V1=self.V1, V2=self.V2, W1=self.W1, W2=self.W2)

    def load_parameters(self, para_type):
        if (para_type == ParameterType.Init):
            print("load init parameters...")
            self.file_name = str.format("{0}/init.npz", self.subfolder)
            w_file = Path(self.file_name)
            if w_file.exists() is False:
                return False
        elif (para_type == ParameterType.Best):
            print("load best parameters...")
            self.file_name = str.format("{0}/best.npz", self.subfolder)
        elif (para_type == ParameterType.Last):
            print("load last parameters...")
            self.file_name = str.format("{0}/last.npz", self.subfolder)
        #endif
        data = np.load(self.file_name)
        self.U1 = data["U1"]
        self.U2 = data["U2"]
        self.V1 = data["V1"]
        self.V2 = data["V2"]
        self.W1 = data["W1"]
        self.W2 = data["W2"]
        return True

    def check_loss(self,X,Y):
        LOSS = 0
        ACC = 0
        for i in range(self.dataReader.num_dev):
            a = self.forward(X[i])
            loss,acc = self.loss_fun.CheckLoss(a, Y[i])
            LOSS += loss
            ACC += acc
        return LOSS/self.dataReader.num_dev, ACC/self.dataReader.num_dev

    def train(self, dataReader, checkpoint=0.1):
        self.dataReader = dataReader
        min_loss = 10
        total_iter = 0
        for epoch in range(self.hp.max_epoch):
            self.hp.eta = self.lr_decay(epoch)
            dataReader.Shuffle()
            while(True):
                # get data
                batch_x, batch_y = dataReader.GetBatchTrainSamples(self.hp.batch_size)
                if (batch_x is None):
                    break
                # forward
                self.forward(batch_x)
                # backward
                self.backward(batch_y)
                # update
                self.update()
                total_iter += 1
            #enf while
            # check loss
            X,Y = dataReader.GetValidationSet()
            loss,acc = self.check_loss(X,Y)
            self.loss_trace.Add(epoch, total_iter, None, None, loss, acc, None)
            print(str.format("{0}:{1}:{2} loss={3:6f}, acc={4:6f}", epoch, total_iter, self.hp.eta, loss, acc))
            if (loss < min_loss):
                min_loss = loss
                self.save_parameters(ParameterType.Best)
            #endif
        #end for
        self.save_parameters(ParameterType.Last)
        self.test(self.dataReader)
        self.loss_trace.ShowLossHistory("Loss and Accuracy", XCoordinate.Epoch)
        self.load_parameters(ParameterType.Best)
        self.test(self.dataReader)
#        self.load_parameters(ParameterType.Last)
#        self.test(self.dataReader)

    def lr_decay(self, epoch):
        if (epoch < 20):
            return 0.005
        elif (epoch < 20):
            return 0.004
        elif (epoch < 40):
            return 0.003
        elif (epoch < 60):
            return 0.002
        elif (epoch < 80):
            return 0.001
        else:
            return 0.0005

    def test(self, dataReader):
        dataReader.ResetPointer()
        confusion_matrix = np.zeros((dataReader.num_category, dataReader.num_category))
        correct = 0
        count = 0
        while(True):
            x,y = dataReader.GetBatchTrainSamples(1)
            if (x is None):
                break
            output = self.forward(x)
            pred = np.argmax(output)
            label = np.argmax(y)
            confusion_matrix[label, pred] += 1
            if (pred == label):
                correct += 1
            count += 1
        #end for
        assert(count == dataReader.num_train)
        print(str.format("correctness={0}/{1}={2}", correct, dataReader.num_train, correct / dataReader.num_train))
        self.draw_confusion_matrix(dataReader, confusion_matrix)

    def draw_confusion_matrix(self, dataReader, confusion_matrix):
        for i in range(dataReader.num_category):
            confusion_matrix[i] = confusion_matrix[i] / confusion_matrix[i].sum()

        # Set up plot
        fig = plt.figure()
        ax = fig.add_subplot(111)
        cax = ax.matshow(confusion_matrix)
        fig.colorbar(cax)

        # Set up axes
        ax.set_xticklabels([''] + dataReader.language_list, rotation=90)
        ax.set_yticklabels([''] + dataReader.language_list)

        # Force label at every tick
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

        # sphinx_gallery_thumbnail_number = 2
        plt.show()


if __name__=='__main__':
    dataReader = load_data()
    eta = 0.005
    max_epoch = 200
    batch_size = 8
    num_input = dataReader.num_feature
    num_hidden1 = 8
    num_hidden2 = 8
    num_output = dataReader.num_category
    model = str.format("Level5_{0}_{1}_{2}_{3}_{4}", max_epoch, batch_size, num_hidden1, num_hidden2, eta)
    hp = HyperParameters_4_4(
        eta, max_epoch, batch_size, 
        dataReader.max_step, num_input, num_hidden1, num_hidden2, num_output, 
        NetType.MultipleClassifier)
    n = net(hp, model)
    n.train(dataReader, checkpoint=1)

