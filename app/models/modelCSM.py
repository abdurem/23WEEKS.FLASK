import torch
import torch.nn as nn

class CSM(nn.Module):
    """
    Convolutional segmentation machine.
    """

    def __init__(self):
        super(CSM, self).__init__()
        self.stage1 = nn.Sequential(nn.Conv2d(1, 8, 9, padding=4),
                                   nn.BatchNorm2d(8),
                                   nn.ReLU(True),
                                   nn.MaxPool2d(2),
                                   nn.Conv2d(8, 8, 9, padding=4, groups=8),
                                   nn.Conv2d(8, 16, 1),
                                   nn.BatchNorm2d(16),
                                   nn.ReLU(True),
                                   nn.MaxPool2d(2),
                                   nn.Conv2d(16, 16, 9, padding=4, groups=16),
                                   nn.Conv2d(16, 32, 1),
                                   nn.BatchNorm2d(32),
                                   nn.ReLU(True),
                                   nn.MaxPool2d(2),
                                   nn.Conv2d(32, 32, 5, padding=2, groups=32),
                                   nn.Conv2d(32, 64, 1),
                                   nn.BatchNorm2d(64),
                                   nn.ReLU(True),
                                   nn.Conv2d(64, 64, 9, padding=4, groups=64),
                                   nn.Conv2d(64, 32, 1),
                                   nn.BatchNorm2d(32),
                                   nn.ReLU(True),
                                   nn.Conv2d(32, 16, 1),
                                   nn.ReLU(True),
                                   nn.Conv2d(16, 1, 1),
                                   nn.Sigmoid())

        self.f1 = nn.Sequential(nn.Conv2d(1, 8, 9, padding=4),
                                nn.BatchNorm2d(8),
                                nn.ReLU(True),
                                nn.MaxPool2d(2),
                                nn.Conv2d(8, 16, 9, padding=4),
                                nn.BatchNorm2d(16),
                                nn.ReLU(True),
                                nn.MaxPool2d(2),
                                nn.Conv2d(16, 32, 9, padding=4),
                                nn.BatchNorm2d(32),
                                nn.ReLU(True))

        self.f2 = nn.Sequential(nn.MaxPool2d(2),
                                  nn.Conv2d(32, 16, 5, padding=2),
                                  nn.BatchNorm2d(16),
                                  nn.ReLU(True))

        self.up = nn.UpsamplingBilinear2d(scale_factor=2)

        self.f3 = nn.Sequential(nn.Conv2d(32, 16, 3, padding=1),
                                  nn.BatchNorm2d(16),
                                  nn.ReLU(True),
                                  nn.Conv2d(16, 16, 3, padding=1),
                                  nn.BatchNorm2d(16),
                                  nn.ReLU(True))

        self.stage2 = CSM_stagen()
        self.stage3 = CSM_stagen()

    def forward(self, x):
        y1 = self.stage1(x)
        x_f1 = self.f1(x)

        x_f2 = self.f2(x_f1)
        x_f3 = self.f3(x_f1)

        x1 = torch.cat([y1, x_f2], 1)
        y2 = self.stage2(x1)
        y2_up = self.up(y2)
        x2 = torch.cat([y2_up, x_f3], 1)
        y3 = self.stage3(x2)

        return y1, y2, y3

class CSM_stagen(nn.Module):
    """
    Network of n(n>=2) stage in CSM.
    """
    def __init__(self):
        super(CSM_stagen, self).__init__()
        self.conv = nn.Sequential(nn.Conv2d(17, 17, 11, padding=5, groups=17),
                                  nn.Conv2d(17, 32, 1),
                                  nn.BatchNorm2d(32),
                                  nn.ReLU(True),
                                  nn.Conv2d(32, 32, 11, padding=5, groups=32),
                                  nn.Conv2d(32, 64, 1),
                                  nn.BatchNorm2d(64),
                                  nn.ReLU(True),
                                  nn.Conv2d(64, 64, 11, padding=5, groups=64),
                                  nn.Conv2d(64, 32, 1),
                                  nn.BatchNorm2d(32),
                                  nn.ReLU(True),
                                  nn.Conv2d(32, 16, 1),
                                  nn.BatchNorm2d(16),
                                  nn.ReLU(True),
                                  nn.Conv2d(16, 1, 1),
                                  nn.Sigmoid())

    def forward(self, x):
        x = self.conv(x)
        return x
