# HTML 周报发布站

这个项目用来把你每周生成的 HTML 文件持续归档到 GitHub，并通过 GitHub Pages 提供一个可选择查看历史内容的网页。

特点：

- 每次新增一个 HTML，不会删除以前的内容
- 首页会自动更新成“可选择查看”的列表
- 推送到 GitHub 后，GitHub Pages 会自动重新发布
- 如果本地已经配置好 `origin` 远程仓库，发布脚本可以顺手帮你 `commit + push`
- 可以安装“自动发布模式”，把 HTML 丢进固定文件夹后自动上传

## 目录结构

```text
.
├── scripts/
│   └── publish_report.py
├── site/
│   ├── assets/
│   ├── data/
│   ├── reports/
│   └── index.html
└── .github/
    └── workflows/
        └── deploy-pages.yml
```

## 第一次使用

1. 当前目录已经初始化成了本地 Git 仓库，分支是 `main`。

如果你之后把这套模板复制到别的空目录，再运行：

```bash
git init -b main
```

2. 在 GitHub 上新建一个空仓库，然后把远程地址加进来：

```bash
git remote add origin git@github.com:你的用户名/你的仓库名.git
```

如果你更习惯 HTTPS，也可以用：

```bash
git remote add origin https://github.com/你的用户名/你的仓库名.git
```

3. 首次推送：

```bash
git add .
git commit -m "Initial site setup"
git push -u origin main
```

4. 推送完成后，在 GitHub 仓库设置里启用 Pages，发布方式选择 GitHub Actions。

参考官方文档：

- GitHub Pages 发布源设置: <https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site>
- 使用 GitHub Actions 发布静态文件: <https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages>

## 每周发布一次 HTML

最简单的理解：

- `~/Desktop/金融学习资料` 是你平时放原始 HTML 的地方
- `publish.command` 是“手动上传按钮”
- 网页地址会显示已经上传成功的 HTML
- 只有“发布过”的文件，才会出现在网页里

最省事的方法是双击根目录里的 `publish.command`，然后把 HTML 文件或整个报告目录拖进去。

也可以直接用命令行：

如果你的报告是单个 HTML 文件：

```bash
python3 scripts/publish_report.py /绝对路径/你的文件.html --title "第12周直播总结" --date 2026-03-24
```

如果你的报告除了 HTML 之外还有配套资源文件（比如图片、CSS、JS），建议把整个目录作为来源：

```bash
python3 scripts/publish_report.py /绝对路径/报告目录 --title "第12周直播总结" --date 2026-03-24
```

如果目录里不是 `index.html`，可以指定入口文件：

```bash
python3 scripts/publish_report.py /绝对路径/报告目录 --entry report.html --title "第12周直播总结"
```

脚本会自动做这些事：

- 复制内容到 `site/reports/`
- 更新首页清单
- 如果当前目录已经是 Git 仓库，会自动 `git add`
- 如果设置了远程仓库 `origin`，会自动 `commit` 并 `push`

如果你习惯双击运行：

```bash
chmod +x publish.command
./publish.command
```

## 自动发布模式

如果你不想每次都双击脚本，可以安装自动发布：

- 桌面会出现一个固定入口：`~/Desktop/自动上传HTML`
- 你只要把 `.html` 文件，或者整个报告目录，放进去
- 大约 1 分钟内会自动发布并推送到 GitHub

安装后，你的日常用法会变成：

1. 把文件放进 `自动上传HTML`
2. 等 1 分钟左右
3. 打开网页首页
4. 点击那份文件的名字，或者点“打开完整 HTML”

日志位置：

- `logs/auto_publish.log`
- `logs/auto_publish.error.log`

如果以后你想关闭自动发布，可以运行：

```bash
./scripts/uninstall_auto_publish_agent.sh
```

## 打开网页

推送到 GitHub 后，Pages 地址通常会是：

```text
https://你的用户名.github.io/你的仓库名/
```

首页会显示全部历史内容，并支持选择某一期查看。

## 注意

- 如果你传入的是单个 HTML 文件，而它依赖同目录下的其他资源文件，请改为直接传入整个目录。
- 发布脚本不会覆盖旧报告；如果标题和日期相同，它会自动补一个编号，避免冲突。
- 本地直接双击打开 `site/index.html` 也能看到列表；正式访问建议用 GitHub Pages。
