# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import numpy as np
from pathlib import Path
from MiniFramework.DataReader_2_0 import *
from MiniFramework.EnumDef_6_0 import *
import random

train_file = '../../Data/ch19_pm25_train.npz'
test_file = '../../Data/ch19_pm25_test.npz'

"""
field: year, month, day, hour, dew, temp, air_press, wind_direction, wind_speed
"""

class PM25DataReader(DataReader_2_0):
    def __init__(self, mode, timestep):
        self.mode = mode    # mode = NetType.Fitting : NetType.MulitpleClassifier
        self.timestep = timestep
        self.train_file_name = train_file
        self.test_file_name = test_file
        self.num_example = 0
        self.num_feature = 0
        self.num_category = 0
        self.num_validation = 0
        self.num_test = 0
        self.num_train = 0

    def ReadData(self):
        super().ReadData()
        if (self.mode == NetType.Fitting):
            self.num_category = 1
            self.YTrainRaw = self.YTrainRaw[:,0].reshape(-1,1)
            self.YTestRaw = self.YTestRaw[:,0].reshape(-1,1)
        elif (self.mode == NetType.MultipleClassifier):
            self.YTrainRaw = self.YTrainRaw[:,1].reshape(-1,1)
            self.YTestRaw = self.YTestRaw[:,1].reshape(-1,1)
            self.num_category = len(npy.unique(self.YTrainRaw))
    
    def Normalize(self):
        super().NormalizeX()
        super().NormalizeY(self.mode)
        # pm2.5 value could not be in XTest, so we use 4-year's average value instead
        #self.SetAveragePollutionValueToXTest()

        self.num_train = self.num_train - self.timestep
        self.XTrain, self.YTrain = self.GenerateTimestepData(self.XTrain, self.YTrain, self.num_train)
        self.num_test = self.num_test - self.timestep
        self.XTest, self.YTest = self.GenerateTimestepData(self.XTest, self.YTest, self.num_test)

    def SetAveragePollutionValueToXTest(self):
        for i in range(self.XTest.shape[0]):
            v = 0
            for j in range(4):
                v += self.YTrain[i+j*365*24,0]
            #end for
            self.XTest[i,0] = v/4
        #end for

    def GenerateTimestepData(self, x, y, count):
        tmp_x = np.zeros((count, self.timestep, self.num_feature))
        tmp_y = np.zeros((count, self.num_category))
        for i in range(count):
            for j in range(self.timestep):
                tmp_x[i,j] = x[i+j]
            #endfor
            tmp_y[i] = y[i + self.timestep]
        #endfor
        return tmp_x, tmp_y

    def GenerateValidationSet(self, k):
        self.num_dev = k
        a = np.random.randint(0, self.num_train, k)
        self.XDev = np.zeros((k, self.XTrain.shape[1], self.XTrain.shape[2]))
        self.YDev = np.zeros((k, self.YTrain.shape[1]))
        for i in range(k):
            self.XDev[i] = self.XTrain[a[i]]
            self.YDev[i] = self.YTrain[a[i]]
