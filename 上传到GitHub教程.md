# 把「点金课表」传到 GitHub，变成一个网址

目标：得到一个类似 `https://你的用户名.github.io/kebiao/` 的网址，发到微信群，同事点开就能查自己的课。

整件事分 5 步，**第一次大概 20 分钟**，之后更新数据只要一条命令（或者干脆让 GitHub 每天自己跑）。

---

## 0. 先搞清楚三件事（避免走弯路）

1. **传上去的是哪几个东西？**
   `index.html`（网页）、`data/`（数据文件夹，里面两个文件）。这两个必须在**仓库最外层**，不能套一层 `点金课表` 文件夹，否则网址会是 `.../kebiao/index.html` 之外再多一层，容易 404。

2. **仓库必须选 Public（公开）。**
   GitHub 免费账号的**私有仓库不能开 Pages**。这个仓库里只有课表，没有课酬，公开没问题。

3. **网址长什么样？**
   `https://你的用户名.github.io/仓库名/` —— 所以仓库名建议用英文，比如 `kebiao`、`dianjin`。

---

## 路线一：网页拖拽上传（不装任何软件，推荐第一次用）

### 1. 注册 / 登录 GitHub

打开 https://github.com ，右上角 `Sign up` 注册（邮箱 + 密码 + 验证码），已有账号直接 `Sign in`。

### 2. 新建仓库

- 右上角 `+` → `New repository`
- **Repository name**：填 `kebiao`（小写英文）
- **Description**：可留空，或填「点金课表」
- 选 **Public**
- 勾上 **Add a README file**
- 点绿色 `Create repository`

### 3. 上传文件

进入刚建好的仓库，页面上有一排按钮，点 **`Add file`** → **`Upload files`**。

然后把这三个东西**从资源管理器直接拖进虚线框**：

```
index.html
data 文件夹（整个拖进去，别只拖里面的文件）
说明.md（可选，别人看不懂时能查）
上传到GitHub教程.md（可选）
```

> 关键：`data` 要**整个文件夹**拖进去。拖完后页面上应该显示成
> `data/all_teachers.js`、`data/all_teachers.json`（带斜杠的路径），而不是两个散落在根目录的文件。
> 如果拖文件夹没反应（有些浏览器不行），见文末「data 文件夹拖不进去怎么办」。

滚到下面 `Commit changes` → 点绿色按钮（提交说明写「初始化」即可）。

### 4. 开启 Pages（生成网址）

- 仓库顶部 **`Settings`**
- 左侧栏往下拉，找到 **`Pages`**
- **Source** 选 **`Deploy from a branch`**
- **Branch** 选 `main`，右边目录选 **`/ (root)`**，点 `Save`
- 等 1–2 分钟，**刷新这个页面**，顶部会出现一条绿底提示：

```
Your site is live at https://你的用户名.github.io/kebiao/
```

点这个网址，应该就能看到「点金课表」了。

### 5. 手机上验一下

把这个网址发到自己的微信「文件传输助手」，点开 → 应该能正常显示、能选老师。
如果手机能开，同事就能开。

---

## 路线二：用 Git 命令上传（之后更新最省事）

适合「以后经常要改数据」的情况。第一次装一下 Git，后面每条命令都很短。

### 1. 装 Git

下载 https://git-scm.com/download/win → 一路 `Next` 默认安装。
装完在开始菜单找 **Git Bash**，打开它。

### 2. 告诉 Git 你是谁（只需一次）

```bash
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 3. 在项目文件夹里初始化

```bash
cd "/c/Users/锋杰呐好美色/Desktop/点金课表"
git init
git add .
git commit -m "初始化点金课表"
```

> 如果提示 `warning: LF will be replaced by CRLF`，忽略即可，不影响。
> 如果 `git add .` 之后 `git status` 里没看到 `.github`，正常，它在隐藏目录里，已经被加进去了。

### 4. 在 GitHub 上建一个空仓库

`+` → `New repository` → 名字 `kebiao` → **Public** → **不要**勾 Add a README（空仓库）→ `Create repository`。

建好后页面会显示仓库地址，形如：

```
https://github.com/你的用户名/kebiao.git
```

### 5. 生成一个「密码」（Personal Access Token）

GitHub 从 2021 年起不接受账号密码推送，必须用 token。步骤：

- 右上角头像 → **`Settings`**
- 左侧最下 → **`Developer settings`**
- **`Personal access tokens`** → **`Tokens (classic)`**
- 右上 **`Generate new token`** → **`Generate new token (classic)`**
- **Note** 填 `kebiao-push`
- **Expiration** 选 `90 days`（到期再生成一个就行）
- **Scopes** 勾上第一个 **`repo`**（勾了它，下面几个会自动勾）
- 拉到底点 `Generate token`
- 页面出现 `ghp_xxxxxxxxxxxx`，**立刻复制保存**（离开页面就再也看不到了）

### 6. 推送

```bash
git branch -M main
git remote add origin https://github.com/你的用户名/kebiao.git
git push -u origin main
```

会弹出登录框（或命令行提示）：

- `Username`：你的 GitHub 用户名
- `Password`：**粘贴刚才那个 ghp_ 开头的 token**（不是账号密码！粘贴时屏幕上不显示字符，是正常的）

推送成功后，回到 GitHub 仓库刷新，文件都在了。

### 7. 以后每天更新，只要三行

```bash
cd "/c/Users/锋杰呐好美色/Desktop/点金课表"
python 生成全员课表.py --refresh
git add . && git commit -m "更新课表" && git push
```

1 分钟后，全网点开都是新数据。

---

## 路线三：GitHub Desktop（图形界面，不想敲命令）

1. 下载 https://desktop.github.com/ 安装，登录你的 GitHub 账号；
2. `File` → `Add local repository` → 选 `桌面/点金课表` → 提示不是仓库时点 `create a repository`；
3. 左下角填提交说明 → `Commit to main` → 右上 `Publish repository`；
4. **取消勾选** `Keep this code private`（否则 Pages 打不开）→ `Publish`；
5. 之后每次更新：`Commit to main` → `Push origin` 两个按钮。

Pages 设置同路线一的第 4 步。

---

## 四、让 GitHub 每天自动更新数据（可选但强烈建议）

配好之后，你什么都不用管：**每天北京时间 06:30**，GitHub 自己去金山文档抓最新课表、
更新 `data/`、自动重新发布网页。同事那边连刷新都不用点 —— 页面每 5 分钟会自己检查一次
（只拉一个 99 字节的 `version.json`），发现新数据就静默换上，并提示「课表已自动更新」。

### 1. 把 Cookie 存进仓库的 Secrets

先拿到 cookie：浏览器打开那份课表 → `F12` → `Network` → 点任意一个请求 →
`Request Headers` → 找到 `Cookie:` 那一整行，复制冒号后面的全部内容。

然后：

- 仓库 → **`Settings`** → 左侧 **`Secrets and variables`** → **`Actions`**
- 点 **`New repository secret`**
- **Name** 填：`WPS_COOKIE`（必须一字不差，全大写）
- **Secret** 填：刚才复制的 cookie 整行
- `Add secret`

### 2. 放入自动更新脚本

仓库里需要有 `.github/workflows/update.yml`。两种放法：

**放法 A（网页手动建，稳）**

- 仓库 → `Add file` → **`Create new file`**
- 文件名输入框里打：`.github/workflows/update.yml`（打 `/` 会自动建目录）
- 把本文件夹里 `.github/workflows/update.yml` 的内容整个粘进去
- `Commit changes`

**放法 B（用 Git）**

本文件夹里已经有这个文件了，路线二推送时会自动带上，不用管。

### 3. 手动跑一次验证

- 仓库顶部 **`Actions`** 标签
- 如果提示要启用，点 `I understand my workflows, go ahead and enable them`
- 左侧选 **`更新课表数据`** → 右边 **`Run workflow`** → 绿色 `Run workflow`
- 等 30–60 秒，出现绿色对勾就是成功；点进去能看到每一步日志
- 回到仓库首页，`data/all_teachers.js` 的提交时间应该刚变过

### 4. 时间说明

`cron: "30 22 * * *"` 是 **UTC 时间**，对应北京时间**每天早上 06:30**。
GitHub 的定时任务在高峰期可能延迟几分钟到半小时，这很正常。
想改时间，用「北京时间 − 8 小时」换算成 UTC：比如想改成 07:00，就写 `0 23 * * *`；
想改成 21:30，就写 `30 13 * * *`。

> 注意：定时任务跑的是 **GitHub 的服务器**，不是你自己的电脑。
> 所以电脑关机、断网都不影响，也不需要在本地装 Python。

### 5. Cookie 过期了怎么办

cookie 一般几周就失效。失效后 Actions 会**变红（失败）**，GitHub 会给你发邮件。
去 `Settings → Secrets` 里点 `WPS_COOKIE` → `Update`，粘一条新的即可。

---

## 五、用 Cloudflare 托管（有 Cloudflare 账号就建议这么做，国内访问快）

GitHub Pages 在国内有时打不开或很慢，微信里点开会转圈。你有 Cloudflare 账号的话，
最舒服的分工是：**GitHub 负责更新数据，Cloudflare 负责发网页**。

```
GitHub 仓库 ──每天 06:30──> Actions 更新 data/ ──push──> Cloudflare Pages 自动重建 ──> 同事打开 pages.dev
```

你不需要改任何代码，数据还是 Actions 生成的，Cloudflare 只是把网页放到离用户更近的节点。

### 1. 前提：仓库已经在 GitHub 上

按上面路线一 / 二 / 三任一做完，`index.html` 和 `data/` 在仓库里就行。

### 2. 在 Cloudflare 建 Pages 项目

- 打开 https://dash.cloudflare.com 登录
- 左侧 **`Workers & Pages`**（新版界面在 `Compute (Workers)` 下面）
- 点 **`Create`** → 选 **`Pages`** → **`Connect to Git`**
- 第一次会要求授权 GitHub：点 `Authorize GitHub` → 选 `Only select repositories` → 勾你的 `kebiao` 仓库
- 选中仓库 → `Begin setup`

### 3. 填构建设置（这一步别填错）

| 字段 | 填什么 |
|---|---|
| Project name | `kebiao`（决定网址 `xxx.pages.dev`，可自定义） |
| Production branch | `main` |
| Framework preset | `None` |
| Build command | **留空**（不要填 `npm build` 之类） |
| Build output directory | `/` |

点 **`Save and Deploy`**，等 20–40 秒。

### 4. 拿到新网址

部署完成会显示 `https://kebiao.pages.dev`（项目名不同，前面那段跟着变）。
这个网址就是发给同事的正式入口。

### 5. 之后全自动

1. GitHub Actions 每天 06:30 更新 `data/` 并 push；
2. Cloudflare 监听到 `main` 有新提交，自动重新部署（30 秒左右）；
3. 同事页面上的版本轮询会在 5 分钟内发现变化，自己换新数据。

整条链路不需要你动手，电脑关机也照跑。

### 6. `_headers` 文件是干什么的

文件夹里有个 `_headers`，是 **Cloudflare Pages 专用**配置（GitHub Pages 会当普通文件忽略，不影响）：

- `/data/version.json` 设 `no-store` —— 必须这样。否则 CDN 缓存这个版本标记，
  网页永远读到旧值，就发现不了更新（表现是"改了数据但页面一直不变"）；
- `/data/*` 设 5 分钟缓存 —— 页面本来就用 `?v=日期` 换地址，够用。

没这个文件也能跑，但容易踩坑，建议一起上传。

### 7. 绑自己的域名（可选）

Pages 项目 → **`Custom domains`** → `Set up a custom domain` → 填 `kebiao.你的域名.com`
→ 按提示在域名 DNS 加一条 CNAME 指向 `kebiao.pages.dev`。
绑好后同事访问自己的域名，好记也更稳。

### 8. 那能不能干脆不用 GitHub，全靠 Cloudflare？

技术上可以（Worker + Cron Triggers 每天抓金山文档），但**不推荐**：

- Workers 免费版每次执行只有 **10ms CPU 时间**，解析一份 250KB 的 xlsx 通常要几百毫秒，会被直接掐断；
- 想稳定得开 Workers Paid（$5/月）；
- 还要把 xlsx 解析库打包进 Worker，维护成本反而更高。

所以分工才是最优解：**GitHub 干重活（跑脚本解析 xlsx），Cloudflare 干轻活（把网页发到各地）**。

---

## 六、把网址发给同事

### 直接发

```
https://你的用户名.github.io/kebiao/
```

同事点开 → 搜自己名字 → 看课。页面会记住他上次选的人。

### 给某个人单独发（直接定位到他）

```
https://你的用户名.github.io/kebiao/?name=段锋杰
https://你的用户名.github.io/kebiao/?name=段锋杰&scope=all
```

`scope=all` 是直接进「全部课表」。中文名字发出去时会自动编码，微信里点开照样能用。

### 做成二维码贴在办公室

把网址粘到任意二维码生成网站（搜「草料二维码」），下载图片打印即可，比让人记网址快。

### 让同事「添加到主屏幕」

- iPhone：Safari 打开 → 分享 → 添加到主屏幕
- 安卓：浏览器菜单 → 添加到桌面

之后就像一个 App，点开直接看。

---

## 七、网页上的「刷新」按钮说明（重要，别误会）

右上角的 **刷新** 按钮做三件事：

1. 重新拉取 `data/all_teachers.json`（带时间戳，绕过浏览器缓存，不会拿到旧文件）；
2. **按「现在」重新计算**今天、未来 7 天的窗口 —— 即使页面开着过夜也不会错位；
3. 把今天**已经上完的课**标灰并加「已上」标签，汇总行显示「今天 2/3 节已上」。

它**不能**直接去金山文档抓数据 —— 网页是纯静态的，浏览器不允许它跨站抓金山文档（也没带你的登录态）。

所以：

| 想达到的效果 | 怎么做 |
|---|---|
| 只是重新算时间、看看最新已发布的数据 | 点网页上的「刷新」 |
| 金山文档改了课，要让网页跟着变 | 电脑上跑 `python 生成全员课表.py --refresh` 再 push，**或者**配好第四节的 Actions 等它自己跑 |

不过大部分时候你**不需要点它**：页面开着时会自己检查更新（见下）。

如果点刷新后提示「数据没变，生成于 11-23 22:15」，说明 GitHub 那边还没更新 —— 去 Actions 看看是不是没跑成功，或者 cookie 过期了。

### 页面的自动同步（不用点也能更新）

- 打开页面时先拉一次数据；8 秒后再核对一次版本，防止命中浏览器缓存；
- 之后每 **5 分钟**拉一次 `data/version.json`（只有 99 字节，几乎不耗流量）；
- 发现 `generatedAt` 变了，就重新拉数据、重算课表，弹一句「课表已自动更新 · 06:30」；
- 切回前台（从微信切回浏览器）时立刻再核对一次。

所以同事早上打开页面之后一直挂着，只要 GitHub 那边 06:30 跑完，他页面最多 5 分钟就自己变了。

---

## 八、常见问题

**打开是 404 / 一片白**

- Pages 刚开要等 1–2 分钟，多刷几次；
- 检查 `index.html` 是不是在仓库**最外层**（路径应为 `/index.html`，不是 `/点金课表/index.html`）；
- 文件名必须是小写 `index.html`，不能是 `Index.html` 或 `index.htm`。

**页面能开但提示「还没有课表数据」**

说明 `data/all_teachers.js` 没上传成功，或者路径不对。
检查仓库里是否存在 `data/all_teachers.js`（注意是 `data` 文件夹里，不是根目录）。

**data 文件夹拖不进去怎么办**

1. 先在仓库点 `Add file` → `Create new file`，文件名打 `data/all_teachers.js`，随便写个 `//` 提交（等于先造出这个目录）；
2. 再 `Add file` → `Upload files`，把两个文件拖进去，此时**在文件名输入框里手动补成** `data/all_teachers.js`、`data/all_teachers.json` 再提交。
   或者更省事：直接用路线二的 Git 命令，`git add .` 一次到位。

**上传了中文名的文件（生成全员课表.py、说明.md）会有问题吗**

不会，GitHub 支持中文文件名。只有一点：Actions 里调用它时要用引号 `python "生成全员课表.py"`，本文件夹的 workflow 已经这么写了。

**Actions 报 `403` / `remote: Permission denied`**

workflow 文件里少了这段（本文件夹的已经带了）：

```yaml
permissions:
  contents: write
```

**Actions 报 `下载失败 HTTP 403` 或 `userNotLogin`**

cookie 过期了。去 `Settings → Secrets` 更新 `WPS_COOKIE`。

**改了数据但网页还是旧的**

- GitHub Pages 有 1 分钟左右的缓存，等一会儿；
- 手机微信内置浏览器缓存更顽固，点右上角「刷新」，或在网址后加 `?v=2` 强制一下。

**国内打开 github.io 很慢 / 打不开**

GitHub Pages 在国内访问不稳定。两个办法：
1. 换 **Cloudflare Pages**（`dash.cloudflare.com` → Workers & Pages → 连同一个仓库，Build command 留空、Output directory 填 `/`），得到 `xxx.pages.dev`，国内一般更顺；
2. 绑定自己的域名（有域名的话最稳）。

**能不能不公开仓库？**

免费账号不行（Pages 需要 Public）。介意的话：删掉 `data/` 里跟课酬无关的东西也没用，因为这个仓库本来就只放了课表数据，没有课酬 —— 课酬在你本地 `workbubby` 那个工具里，从来不会上传。

---

## 九、传完之后仓库应该长这样

```
kebiao/
├── .github/workflows/update.yml   每天自动更新（可选）
├── index.html                     网页
├── _headers                       Cloudflare Pages 的缓存配置（GitHub Pages 忽略）
├── data/
│   ├── all_teachers.js            网页加载的数据
│   ├── all_teachers.json          标准 JSON
│   └── version.json               99 字节版本标记，网页靠它自动发现更新
├── 生成全员课表.py                 数据生成脚本（在 Actions 的服务器上跑）
├── 说明.md
└── 上传到GitHub教程.md
```

只要 `index.html` 和 `data/` 到位，网页就能用；`生成全员课表.py` 和 `.github/` 是给自动更新用的。
