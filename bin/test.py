#!/usr/bin/env python

import cv

im = cv.LoadImage("./0412/45.8-1/bg.png", cv.CV_LOAD_IMAGE_COLOR)
im2 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
cv.ConvertScale(im, im2, 1.0)
cv.ShowImage("image", im)
cv.WaitKey(0)
cv.ShowImage("image", im2)
cv.WaitKey(0)
