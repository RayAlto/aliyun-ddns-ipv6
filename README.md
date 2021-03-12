# aliyun-ddns-ipv6

用阿里云的域名搭建动态DNS，只适用于ipv6地址。

## 1. 部署域名和管理账号

去![这里](https://dc.console.aliyun.com/next/index#/domain/list/all-domain)登陆后确认好你要使用的二级域名，然后去![这里](https://ram.console.aliyun.com/manage/ak)整一个AccessKey，确保有管理云解析的权限，然后去![这里](https://next.api.aliyun.com/api/Alidns/2015-01-09/DescribeSubDomainRecords?tab=DEBUG)填好你的信息拿到`RecordId`。

## 2. 填写配置文件

配置文件需要放在工作目录：

* `ServerChanKey`: 解析更新后可以设置发送Server酱，不需要可以填`null`
* `AccessKeyId`: 刚刚拿到的AccessKey的ID
* `AccessKeySecret`: 刚刚拿到的AccessKey的密码
* `DomainName`: 你的域名，比如"fuck.me"
* `RecordId`: 刚刚拿到的RecordId
* `RR`: 你的二级域名，比如你想要设置域名"oh.fuck.me"为ddns，那这里就填"oh"
* `RecordType`: 填"AAAA"，表示ipv6，目前只支持着一种类型

## 3. 定时运行

为了方便可以先写一个脚本：

```shell
#!/usr/bin/sh

cd /path/to/this/directory
/usr/bin/python ddns.py
```

然后随便找一个定时任务管理器，比如`systemd`的用户服务：

```shell
vim /home/$USER/.config/systemd/user/ddns.timer
```

把下面的内容放进去

```systemd
[Unit]
Description=DDNS

[Timer]
OnCalendar=minutely
Persistent=true

[Install]
WantedBy=timers.target
```

就可以实现每分钟启动`ddns`服务，然后填写服务配置

```shell
vim /home/$USER/.config/systemd/user/ddns.service
```

把下面的内容放进去

```systemd
Unit]
Description=DDNS

[Service]
Type=oneshot
ExecStart=/path/to/the/script
```

写好后enable上面的timer就可以了：

```shell
systemctl --user enable ddns.timer
```
