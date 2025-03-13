# Akile 自动签到工具
## 如果可以点个Star 谢谢各位了！！！
这是一个用于 Akile 平台的自动签到工具，可以帮助用户每天自动完成签到操作。

# 请不要使用定时功能，暂时无法使用！！！

## 功能特点

- 支持一次性签到或定时自动签到
- 可从命令行参数或文件中读取授权令牌
- 详细的日志记录
- 用户信息获取和展示
- 自动处理Cloudflare防护

## 安装依赖

使用 pip 安装必要的依赖：

```bash
pip install -r requirements.txt
```

或手动安装以下依赖：

```bash
pip install selenium webdriver-manager schedule
```

## 前置条件

- Python 3.6 或更高版本
- Google Chrome 浏览器（脚本会自动下载对应版本的ChromeDriver）

## 使用方法

### 基本用法

1. 使用授权令牌一次性签到：

```bash
python auto_checkin.py -t "你的授权令牌" --once
```

2. 从文件读取授权令牌并一次性签到：

```bash
# 先将授权令牌保存到文件中
echo "你的授权令牌" > token.txt
python auto_checkin.py -f token.txt --once
```

### 高级选项

1. 将授权令牌保存为文件，方便后续使用：

```bash
python auto_checkin.py -t "你的授权令牌" -o token.txt
```

### 定时签到

1. 使用默认时间（每天早上8:30）定时签到：

```bash
python auto_checkin.py -t "你的授权令牌"
```

2. 自定义签到时间：

```bash
python auto_checkin.py -t "你的授权令牌" -s "12:00"
```

## 获取授权令牌

授权令牌可以通过以下步骤获取：

1. 登录 Akile 网站 (https://akile.io/)
2. 打开浏览器开发者工具（F12）
3. 切换到"应用"(Application)或"存储"(Storage)选项卡
4. 在左侧找到"本地存储"(Local Storage)
5. 点击网站域名，在右侧找到"token"项
6. 复制该值作为授权令牌

也可以从网络请求中获取：

1. 打开开发者工具（F12）
2. 切换到"网络"(Network)选项卡
3. 刷新页面，找到任意API请求
4. 查看请求头中的 "Authorization" 字段的值

## 命令行参数说明

| 参数 | 短参数 | 说明 |
|------|-------|------|
| `--token` | `-t` | 指定授权令牌 |
| `--token-file` | `-f` | 指定包含授权令牌的文件路径 |
| `--schedule` | `-s` | 设置每日定时签到时间 (格式: HH:MM) |
| `--once` | 无 | 仅执行一次签到而不是持续运行 |
| `--save-token` | `-o` | 将授权令牌保存到指定文件 |

## 故障排除

- **SSL错误**: 如果遇到SSL错误，脚本已经配置为忽略SSL证书验证。
- **签到失败**: 检查令牌是否有效，或者尝试重新获取新的令牌。
- **ChromeDriver错误**: 脚本会自动下载与Chrome浏览器版本匹配的驱动，请确保Chrome浏览器已安装。

## 注意事项

- 授权令牌有效期通常较长，但不是永久的，如果签到失败，请检查令牌是否过期
- 为保证账号安全，请勿将授权令牌分享给他人
- 该脚本仅供学习和个人使用
- 脚本需要安装Chrome浏览器才能运行


# 更多内容可以访问:blog.smlin0513.asia

## 开源许可

MIT 