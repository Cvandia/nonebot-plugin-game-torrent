<div align="center">

<a href="https://v2.nonebot.dev/store"><img src="./res/image.png" width="180" height="180" alt="NoneBotPluginLogo" style="border-radius: 50%;"></a>

</div>

<div align="center">

# nonebot-plugin-game-torrent

_⭐基于Nonebot2的获取游戏种子插件⭐_


</div>

<div align="center">
<a href="https://www.python.org/downloads/release/python-390/"><img src="https://img.shields.io/badge/python-3.8+-blue"></a>  <a href=""><img src="https://img.shields.io/badge/QQ-1141538825-yellow"></a> <a href="https://github.com/Cvandia/nonebot-plugin-game-torrent/blob/main/LICENCE"><img src="https://img.shields.io/badge/license-MIT-blue"></a> <a href="https://v2.nonebot.dev/"><img src="https://img.shields.io/badge/Nonebot2-2.0.0rc1+-red"></a>
</div>

---

## ⭐ 介绍

为用户在线提供游戏种子资源

## 📜 免责声明

> [!CAUTION]
> 本插件仅供**学习**和**研究**使用，使用者需自行承担使用插件的风险。作者不对插件的使用造成的任何损失或问题负责。请合理使用插件，**遵守相关法律法规。**
使用本插件获取游戏种子资源可能涉及到**版权问题**，请在使用过程中遵守相关法律法规，**不要传播盗版游戏**或侵犯他人权益的内容。使用者应自行承担因违反法律法规而产生的**法律责任**。
本插件提供的游戏种子资源仅供**个人使用**，不得用于**商业目的**。使用者应自行判断是否符合使用条件，并承担因使用不当而产生的一切后果。
使用**本插件即表示您已阅读并同意遵守以上免责声明**。如果您不同意或无法遵守以上声明，请不要使用本插件。


## 💿 安装

<details>
<summary>安装</summary>

pip 安装

```
pip install nonebot-plugin-game-torrent
```
- 在nonebot的pyproject.toml中的plugins = ["xxx"]添加此插件

nb-cli安装

```
nb plugin install nonebot-plugin-game-torrent -U
```

git clone安装(不推荐)

- 命令窗口`cmd`下运行
```bash
git clone https://github.com/Cvandia/nonebot-plugin-game-torrent
```
- 在窗口运行处
将文件夹`nonebot-plugin-torrent-game`复制到bot根目录下的`src/plugins`(或创建bot时的其他名称`xxx/plugins`)


 </details>

 <details>
 <summary>注意</summary>

 推荐镜像站下载

 清华源```https://pypi.tuna.tsinghua.edu.cn/simple```

 阿里源```https://mirrors.aliyun.com/pypi/simple/```

</details>

## ⚙️ 配置

**在env.中添加以下配置**

|        配置         | 类型  | 必填项 |                                      默认值                                       |             说明             |
| :-----------------: | :---: | :----: | :-------------------------------------------------------------------------------: | :--------------------------: |
| torrent_send_format |  str  |   否   | "game: {game_name}\nsize: {size}\nlast_update: {last_update}\nmagnet: {magnet}\n" |        默认发送的格式        |
|  magnet_to_qrcode   | bool  |   否   |                                       False                                        | 是否将magnet链接转换为二维码 |

## ⭐ 使用

### 指令：
> **注**: 以下命令均为command触发,实际需要在命令前加上`command_start`

|   指令   | 需要内容 |    范围    |     说明     |  权限  |
| :------: | :------: | :--------: | :----------: | :----: |
| 游戏搜索 |    是    | 群聊、私聊 | 搜索游戏种子 | 所有人 |
|  种子源  |    否    | 群聊、私聊 |  管理种子源  | 所有人 |

### 示例：

- `/游戏搜索 赛博朋克2077`
- `/搜索游戏 艾尔登法环`
- `/种子源 show`
- `/源 change 1`

## 🌙 未来
 - [x] 获取种子链接供下载
 - [x] 链接转二维码
 - [ ] 上传群文件
 - [ ] 配置下载种子文件路劲
 ~~- [ ] 添加更多种子获取网站~~
- [x] 添加[Aimhaven](https://aimhaven.com/)的种子获取

<center>喜欢记得点个star⭐</center>

## 💝 特别鸣谢

- [x] [nonebot2](https://github.com/nonebot/nonebot2): 本项目的基础，非常好用的聊天机器人框架。
