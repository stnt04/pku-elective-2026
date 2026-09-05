# PKUAutoElective2023-dddd

北大选课网 **补退选** 阶段自动选课小工具 (2023.05.20)

- 更新了**验证码识别模型**，使用 CNN+LSTM+CTC 的经典网络识别不定长验证码（4~5 个字符），训练过程使用了项目[dddd_trainer](https://github.com/sml2h3/dddd_trainer)

- 适配 2023 年秋季学期北大选课网环境，目前支持 `本科生（含辅双）` 和 `研究生` 选课

本项目在 [zhongxinghong/PKUAutoElective](https://github.com/zhongxinghong/PKUAutoElective)上进行修改，仅将验证码识别模型进行替换，使用该工具**只需要安装 ddddocr 库**（已放在 requirements.txt 文件中，可以通过 pip 安装），而**不必安装 Pytorch 和 TensorFlow**。其余使用方法参照原项目

---

## 本版本改动（2026 秋季硕士生选课）

在 `zhongxinghong/PKUAutoElective` / `PKUAutoElective2023-dddd` 基础上的**本地更新版**，用于 2026 秋季硕士生选课：

1. **适配 Python 3.14**：更新依赖、修复 numpy 2.x 兼容。
2. **验证码识别更准**：改用 ddddocr 默认模型（原自定义模型准确率偏低）。
3. **新增图形化配置界面**：`python gui.py`，可配置课程、后台运行、实时查看日志。

其余使用方法参照原项目。

---

## 模型性能：

- 该项目的验证码识别模型使用 Python3.8.16，Pytorch 环境下进行训练和测试
- 使用 74.5w 张图片进行训练，测试集上能达到 98%的准确率。
- 使用 cpu 识别单张图片平均耗时 5-20ms，准确率和耗时均优于打码平台。
- 使用时无需安装 Pytorch 和 TensorFlow

ps: 验证码训练集使用 Kaptcha 工具模仿生成（图片样例见[test/data](./test/data)），在选课网上能达到较高的准确率（96%以上），该模型也可以作为预训练模型或用于自举（[bootstrap.py](./bootstrap.py)，该代码参考了项目：[https://github.com/zhongxinghong/PKUElectiveCaptcha2021Spring](https://github.com/zhongxinghong/PKUElectiveCaptcha2021Spring/blob/master/bootstrap.py))

---

## 注意事项

特地将一些重要的说明提前写在这里，希望能得到足够的重视

1. 不要使用过低的刷新间隔，以免对选课网服务器造成压力，建议时间间隔不小于 4 秒
2. 选课网存在 IP 级别的限流，访问过于频繁可能会导致 IP 被封禁

---

## 项目安装

（以下是对 zhongxinghong 大佬项目[https://github.com/zhongxinghong/PKUAutoElective](https://github.com/zhongxinghong/PKUAutoElective)使用说明的修改，主要是说明**安装过程**，更多细节请参照原项目）

### Python 3

该项目至少需要 Python 3，可以从 [Python 官网](https://www.python.org/downloads/) 下载并安装（原开发环境为 Python 3.8.16；本版本已适配并实测于 **Python 3.14**，requirements.txt 中的依赖已更新为 3.14 兼容版本，若用其它版本请以其依赖为准）

例如在 Linux 下运行：

```console
$ apt-get install python3
```

在 Windows 上可以在 Python 官网下载

### Repo

下载这个 repo 至本地。点击右上角的 `Code -> Download ZIP` 即可下载

（或）对于 git 命令行：

```console
$ git clone https://github.com/Hovennnnn/PKUAutoElective.git
```

### Packages

安装依赖包（该示例中使用清华镜像源以加快下载速度，“项目的路径”因人而异）

命令行运行：

```console
$ cd 项目的路径
$ pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

- 你把文件下载在哪，上面命令行里“项目的路径”这里就写啥，比如我的项目路径是：C:\Users\123\Documents\codefield\python_code\PKUAutoElective）
- 关于"cd"命令是什么，可以参考[Wikipedia](<https://zh.wikipedia.org/zh-sg/Cd_(命令)>)的解释
- 前面"$"符号不用输入，它表示终端的提示符

### 验证码识别模块测试

这个测试旨在检查与验证码识别模块相关的依赖包是否正确安装。命令行运行：

```console
$ cd test/
$ python3 test_cnn.py
```

显示：

```
Captcha('2a2m') True 耗时:  9.960195541381836 ms
Captcha('2a3cx') True 耗时:  4.985332489013672 ms
Captcha('2a5c') True 耗时:  3.984689712524414 ms
Captcha('2anwx') True 耗时:  4.983425140380859 ms
Captcha('2ega') True 耗时:  2.9973983764648438 ms
Captcha('cecc') True 耗时:  5.973339080810547 ms
Captcha('dnwp6') True 耗时:  8.748054504394531 ms
Captcha('dnynw') True 耗时:  3.619670867919922 ms
Captcha('dp4y') True 耗时:  4.810333251953125 ms
Captcha('mgmn') True 耗时:  5.278110504150391 ms
Captcha('mgnd') True 耗时:  5.984067916870117 ms
Captcha('n4efg') True 耗时:  3.983020782470703 ms
Captcha('n5edf') True 耗时:  4.983663558959961 ms
Captcha('n6ad') True 耗时:  6.6471099853515625 ms
Captcha('nnman') True 耗时:  2.988100051879883 ms
Captcha('penn') True 耗时:  3.987550735473633 ms
Captcha('pf32') True 耗时:  3.9911270141601562 ms
Captcha('wd54') True 耗时:  5.372762680053711 ms
Captcha('wd55m') True 耗时:  3.982067108154297 ms
Captcha('wda3') True 耗时:  3.978252410888672 ms
```

## 责任须知

- 你可以修改和使用这个项目，但请自行承担由此造成的一切后果
- 严禁在公共场合扩散这个项目，以免给你我都造成不必要的麻烦

---

再次鸣谢各位前辈对该项目的贡献！
