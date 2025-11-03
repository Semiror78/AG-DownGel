基于 PyQt6 的跨平台 GUI 下载器，用于从 GelBooru.com 搜索和批量下载图像、GIF 和视频，支持标签过滤、AI 排除和组织存储。

## 功能
- **标签搜索**：输入空格分隔标签（例如 `catgirl solo`）；支持 GelBooru 语法如 `rating:explicit`。
- **文件过滤**：选择图像（.jpg、.png 等）、GIF 或视频（.mp4、.webm）；下载到子文件夹（`images/`、`GIF/`、`videos/`）。
- **AI 排除**：复选框添加 `-ai-generated` 以排除 AI 内容。
- **API 支持**：可选 User ID/API Key 以提高限制（从 [GelBooru 账户](https://gelbooru.com/index.php?page=account&s=options) 获取）。
- **本地化**：英语（默认）、俄语、中文、日语；通过 `locales/*.json` 扩展。
- **下载**：保存到 `downloads/[清理标签]/` 以便组织。
- **进度和错误**：实时状态，分页时不确定进度。

## 安装
1. 确保 Python 3.10+ 并安装依赖：  
2. pip install PyQt6 requests
3. 运行：`python main.py`（如需重命名脚本）。
4. 自动创建文件夹：`downloads/`（输出）和 `locales/`（翻译）。

## 使用
1. 从下拉菜单选择语言（顶部）。
2. 在搜索字段输入标签（例如 `brazilian_miku hatsune_miku feet`）。
3. 选中“无 AI”以排除 AI 生成内容。
4. 选择文件类型。
5. （可选）输入 User ID 和 API Key。
6. 点击“下载全部” – 文件保存到 `downloads/[标签]/`。
![alt text](https://github.com/Semiror78/AG-DownGel/blob/main/api.png?raw=true)


## 示例标签
来自 `guide.txt`：

**Kasane_teto -hatsune_miku rating:explicit**  
(下载 teto 无 miku，含 18+ 内容)

**评级选项：**  
- `rating:explicit` (NSFW)  
- `rating:questionable` (边界)  
- `rating:sensitive` (成熟)  
- `rating:general` (安全)

## 故障排除
- **0 帖子？** 添加相关标签（例如为 `brazilian_miku` 添加 `hatsune_miku`）；检查 GelBooru [DAPI 文档](https://gelbooru.com/index.php?page=help&topic=dapi)。
- **速率限制：** 使用 API Key 以 >100 结果/页。
- **自定义语言：** 添加 `locales/[lang].json`，键匹配 `en.json`。

## 许可
MIT 许可 – 免费使用/修改。
