[中文 README](/README.md) | [English README](/doc-en/README.md)

# AUR 自动发布

本文档说明如何通过 GitHub Actions 将 MMLang 自动同步到 [AUR](https://aur.archlinux.org/packages/mmlang)。工作流只负责更新 `PKGBUILD` / `.SRCINFO` 并推送到 AUR，不在 CI 中构建二进制包。

## 产物

- `PKGBUILD` (`/PKGBUILD:1`)：`pkgname=mmlang`，`source` 拉取 `https://github.com/aura-deak/MMLang/archive/refs/tags/v$pkgver.tar.gz`，`depends=('python' 'python-bitarray')`（`PKGBUILD:9`），`package()` 将 `common.py/asm_core.py/vm_core.py` 等安装至 `/usr/share/mmlang` 并创建 `/usr/bin/mmlang-asm|run|debug`。
- `.SRCINFO` (`/.SRCINFO:1`)：AUR 元数据，由工作流从 `PKGBUILD` 解析生成（无需 `makepkg`），随 `PKGBUILD` 同步更新。
- 工作流 `.github/workflows/aur-publish.yml`：仅在 `release: published`（GitHub Release 发布）与 `workflow_dispatch` 时触发，仅做版本/哈希更新与 AUR 推送（`push` 标签不再直接触发）。

## 首次发布（创建 AUR 包）

若 `aur@aur.archlinux.org:mmlang.git` 为空，工作流会在 `Push to AUR` 步骤自动 `git init` 并 `push HEAD:master`。也可手动初始化：

```bash
git clone ssh://aur@aur.archlinux.org/mmlang.git /tmp/aur-mmlang
cp PKGBUILD .SRCINFO /tmp/aur-mmlang/
cd /tmp/aur-mmlang
git add PKGBUILD .SRCINFO
git commit -m "Initial import 1.0.0.1"
git push origin master
```

需先在 AUR 注册账号并在 **My Account → SSH Public Key** 添加公钥。

## 配置 GitHub Secrets

在 `aura-deak/MMLang` 的 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 |
|---|---|
| `AUR_SSH_PRIVATE_KEY` | AUR 私钥全文（`-----BEGIN OPENSSH PRIVATE KEY-----`）。对应公钥需已贴到 AUR。建议 `ssh-keygen -t ed25519 -C "aur@mmlang"`，不要设 passphrase。 |

AUR SSH 统一使用 `aur` 用户（`ssh://aur@aur.archlinux.org/mmlang.git`）。

> 未配置该 Secret 时工作流为 **dry-run**：仅更新本地 `PKGBUILD`/`.SRCINFO` 并打印，不推送到 AUR。

## 发布流程

### 自动（推荐）

```bash
git commit -am "feat: ..."
git push origin main
git tag v1.0.0.2 -m "Release v1.0.0.2"
git push origin v1.0.0.2
# 然后在 GitHub 创建 Release（选择同名 tag v1.0.0.2 → Publish release）才会触发 AUR 同步
# 单独推送 tag 不会触发（工作流已改为 on: release）

# 工作流在 Release 发布后将：
# - 下载 https://github.com/aura-deak/MMLang/archive/refs/tags/v1.0.0.2.tar.gz
# - 计算 sha256 并更新 PKGBUILD 的 sha256sums
# - 从 PKGBUILD 生成 .SRCINFO（纯 bash，无需 Arch 容器/makepkg）
# - 推送到 AUR master
```

### 手动触发

GitHub **Actions → Publish to AUR → Run workflow**，可输入 `tag`（如 `v1.0.0.2`），留空则取 `git describe` 最新标签。

### 仅更新 pkgrel

同版本修复打包脚本时手动改 `PKGBUILD:4` 的 `pkgrel`，工作流对新版本会自动重置为 `1`，同版本补丁需手动递增并重新触发。

## 本地验证（可选）

```bash
# 检查 PKGBUILD 语法与哈希
curl -L -o /tmp/source.tar.gz https://github.com/aura-deak/MMLang/archive/refs/tags/v1.0.0.1.tar.gz
sha256sum /tmp/source.tar.gz

# 如已安装 pacman/makepkg，可本地生成 .SRCINFO 校验（非必需，工作流已用 bash 生成）
makepkg --printsrcinfo > /tmp/check.srcinfo && diff -u .SRCINFO /tmp/check.srcinfo
```

用户侧安装（发布后）：

```bash
yay -S mmlang
# 或 paru -S mmlang
# 或 git clone https://aur.archlinux.org/mmlang.git && cd mmlang && makepkg -si
```

## 工作流细节

- 运行环境：`ubuntu-latest`（无 `archlinux` 容器，无 `base-devel/makepkg/namcap`，仅做上传更新）。
- 触发条件：`on.release.types: [published]`（仅 Release 发布，`push` 标签不触发）+ `workflow_dispatch` 手动输入 tag。
- 版本探测（`aur-publish.yml:22`）：`inputs.tag` > `release.tag_name` > `refs/tags/*`（兼容手动）> `git describe`。
- 更新逻辑：`sed` 改 `pkgver/pkgrel`，`curl` 下载 tarball 求 `sha256sum`，`sed` 改 `sha256sums`，再用 bash 从 `PKGBUILD` 解析 `pkgdesc/url/license` 生成 `.SRCINFO`。
- SSH：`~/.ssh/aur` 私钥 + `ssh-keyscan aur.archlinux.org`，`Host aur.archlinux.org User aur`。
- 推送：`ssh://aur@aur.archlinux.org/mmlang.git` 的 `master` 分支。
- 回写：若 `PKGBUILD/.SRCINFO` 有变更且非 detached HEAD，尝试 `git push origin HEAD`（需 `contents: write`）。

## 常见问题

**Q: 提示 `AUR_SSH_PRIVATE_KEY not set`？**  
A: dry-run 模式，配置私钥后重跑。

**Q: `Permission denied`？**  
A: 检查私钥包含 `BEGIN/END` 全文本、公钥已在 AUR 生效、密钥为 `ed25519`。

**Q: 已推送 tag 但 AUR 未更新？**  
A: 本工作流已改为仅 `release` 触发，单推 tag 不会执行。需在 GitHub 创建 Release（`Releases → Draft a new release → 选择 tag → Publish release`）或使用 `workflow_dispatch` 手动输入 tag。若仍无更新，查看 `Push to AUR` 日志是否 `No changes to push`。

## 相关文件

- `PKGBUILD`、`.SRCINFO`、`doc/aur-publish.md`
- 工作流：`.github/workflows/aur-publish.yml`
