#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: test_cnn.py
# Created Date: 2021-03-10
# Edited Date: 2023-05-20
# Author: Rabbit, Hovennnn
# --------------------------------
# Copyright (c) 2021 Rabbit

import sys
sys.path.append("../")

import os
import time
from autoelective.captcha import CaptchaRecognizer
from autoelective.const import CNN_MODEL_FILE, CAPTCHA_LABELS_FILE


def test_captcha(r, code=None):
    # 遍历data目录下的所有验证码图片
    if(code is None):
        for root, dirs, files in os.walk('./data'):
            for file in files:
                if file.endswith(".jpg"):
                    code = file.split("_")[0]
                    filepath = os.path.join(root, file)
                    with open(filepath, 'rb') as fp:
                        im_data = fp.read()

                    start_time = time.time()
                    c = r.recognize(im_data)
                    print(c, c.code == code, "耗时: ", (time.time() - start_time) * 1000, "ms")
    else:
        for root, dirs, files in os.walk('./data'):
            for file in files:
                if file.endswith(".jpg") and file.startswith(code):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'rb') as fp:
                        im_data = fp.read()

                    start_time = time.time()
                    c = r.recognize(im_data)
                    print(c, c.code == code, "耗时: ", (time.time() - start_time) * 1000, "ms")
                    break

def main():
    r = CaptchaRecognizer(CNN_MODEL_FILE, CAPTCHA_LABELS_FILE)
    test_captcha(r)

if __name__ == "__main__":
    main()
