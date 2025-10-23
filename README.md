# 椰椰电竞 - 游戏合集 🎮

两款炫酷的科幻风格小游戏，采用三角洲行动主题设计。

## 🎮 在线体验

- **游戏合集首页**: [https://你的用户名.github.io/yeye-game/home.html](https://你的用户名.github.io/yeye-game/home.html)
- **扫雷游戏**: [https://你的用户名.github.io/yeye-game/index.html](https://你的用户名.github.io/yeye-game/index.html)
- **翻翻乐游戏**: [https://你的用户名.github.io/yeye-game/flipcard.html](https://你的用户名.github.io/yeye-game/flipcard.html)

> 部署后记得将上面的 `你的用户名` 替换为你的 GitHub 用户名

## ✨ 游戏特色

### 🏠 游戏合集首页
- 🎨 统一入口，一个页面访问所有游戏
- 🖼️ 精美背景图片设计
- 📱 响应式卡片，炫酷悬停动画
- ⚡ 一键进入对应游戏

### 💣 扫雷游戏
- 🌟 三角洲行动科幻风格
- 📱 完美适配移动端
- 🎯 多种难度：9/12/16/22次扫雷
- 💎 实时数据统计
- 💾 支持导出/导入游戏进度

### 🎴 翻翻乐游戏
- 🖼️ 真实图片卡片（29张精美图片）
- 📍 位置编号显示
- 🎯 三种难度：简单/中等/困难
- ⏱️ 完整统计：时间、翻牌次数、配对数
- 💰 保底管理系统
- 💾 数据持久化

## 🚀 快速开始

### 方式一：在线访问（推荐）

访问 GitHub Pages 部署的在线版本（见上方链接）

### 方式二：本地运行

1. **克隆仓库**
```bash
git clone https://github.com/你的用户名/yeye-game.git
cd yeye-game
```

2. **启动本地服务器**

**方法1：使用 Python**
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000
```

**方法2：使用 Node.js**
```bash
npx serve
```

**方法3：使用 PHP**
```bash
php -S localhost:8000
```

3. **访问游戏**
```
浏览器打开：http://localhost:8000/home.html
```

## 📂 项目结构

```
yeye-game/
├── home.html                # 游戏合集首页
├── index.html               # 扫雷游戏
├── flipcard.html            # 翻翻乐游戏
├── beijingtu.jpg            # 背景图片
├── hong/                    # 翻翻乐卡片图片（29张）
│   ├── bijiben.png
│   ├── buzhanche.png
│   └── ...
├── README.md                # 项目说明
└── .gitignore              # Git 忽略配置
```

## 🎮 游戏规则

### 扫雷游戏规则
- 固定 **7×7 网格**（49个格子）
- 选择扫雷次数：9/12/16/22 次
- 初始保底：**1000W**
- 踩到炸弹💣：保底 **-300W**
- 翻到数字：累计到出红数
- 支持随时导出/导入进度

### 翻翻乐游戏规则
- 选择难度：
  - 简单：4×5（20张牌）- 保底 3688W
  - 中等：5×6（30张牌）- 保底 6688W
  - 困难：5×10（50张牌）- 保底 16688W
- 每次翻开两张牌，相同图片保持翻开
- 配对所有卡片即可获胜
- 支持保底管理和历史记录

## 🛠️ 技术栈

- **纯原生技术**：HTML5 + CSS3 + JavaScript (ES6+)
- **无需框架**：零依赖，单文件即可运行
- **响应式设计**：完美适配手机、平板、电脑
- **科幻UI**：Orbitron 字体 + 霓虹发光效果
- **数据持久化**：LocalStorage + JSON 导出导入

## 📱 移动端支持

所有游戏都完美支持移动端：

- ✅ 触摸友好的操作
- ✅ 自适应屏幕尺寸
- ✅ 优化的按钮和文字大小
- ✅ 流畅的动画效果

测试设备：iPhone、Android、iPad

## 🎨 特色功能

### 数据导入导出
- 📤 随时导出游戏进度（JSON格式）
- 📥 导入之前的存档继续游戏
- 💾 支持多个存档，不同难度分别保存

### 保底管理（翻翻乐）
- ➕ 增加保底
- ➖ 减少保底
- 📝 查看变动历史（含北京时间）

### 科幻主题
- 🌟 三角洲行动游戏风格
- 💫 霓虹发光特效
- 🎨 深色主题 + 渐变背景
- ✨ 流畅的动画效果

## 📦 部署到 GitHub Pages

1. **在 GitHub 上创建仓库** `yeye-game`

2. **推送代码**
```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/yeye-game.git
git push -u origin main
```

3. **开启 GitHub Pages**
   - 进入仓库 Settings → Pages
   - Source 选择 `main` 分支
   - 点击 Save
   - 等待几分钟后访问：`https://你的用户名.github.io/yeye-game/home.html`

## 🌐 其他部署方式

### Vercel（推荐）
```bash
npm i -g vercel
vercel
```

### Netlify
直接拖拽项目文件夹到 [Netlify Drop](https://app.netlify.com/drop)

### Gitee Pages（国内访问快）
1. 导入到 Gitee
2. 开启 Gitee Pages 服务
3. 访问：`https://你的用户名.gitee.io/yeye-game`

## 🎯 更新日志

### V4.0 (2025-10-23)
- ✅ 新增游戏合集首页
- ✅ 扫雷游戏支持导入/导出
- ✅ 统一背景图片设计
- ✅ 完美移动端支持
- ✅ 优化翻翻乐提示文本格式

### V3.1
- ✅ 翻翻乐保底管理优化
- ✅ 变动记录模态框

### V3.0
- ✅ 翻翻乐导入/导出功能
- ✅ 图片卡片系统

### V2.0
- ✅ 翻翻乐游戏上线

### V1.0
- ✅ 扫雷游戏上线

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习交流使用。

## 💬 联系方式

如有问题或建议，欢迎通过 GitHub Issues 反馈。

---

**椰椰电竞 YEYE CLUB © 2025**  
**DELTA EXCLUSIVE PRICE LIST**  
**祝你游戏愉快！** 🎮✨
