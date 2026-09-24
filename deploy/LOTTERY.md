# 抽奖站部署与运营

抽奖页面是 `lottery.html`，由现有 `yeye-nginx` 提供静态文件，抽奖 API 由独立容器提供。按 [Nginx 部署说明](DEPLOY.md) 将 Nginx 和 API 接入共享的 `yeye-lottery` Docker 网络；Compose 不会启动第二个 Nginx，也不映射 API 端口到公网。

## 初始化与启动

首次部署时创建共享网络，并把已运行的 Nginx 容器接入一次：

```bash
docker network create yeye-lottery
docker network connect yeye-lottery yeye-nginx
```

若 `yeye-nginx` 是新建容器，则创建容器时使用 `--network yeye-lottery`，无需再执行 `network connect`。在仓库根目录启动 API：

```bash
docker compose -f deploy/lottery.compose.yml up -d --build
```

API 初始化时会创建数据库和奖池。数据库位于 Docker 卷 `yeye_lottery_data`；升级时保留该卷并定期备份。不要将数据库或券码文件放进 `/home/ubuntu/yeye/nginx/html` 等公开网页目录。

## 生成与管理兑奖码

例如生成 100 张码并输出到私有数据卷中的 TXT 文件（每行一张）：

```bash
docker compose -f deploy/lottery.compose.yml run --rm lottery-api python app.py generate 100 --output /data/codes-100.txt
```

生成命令不会覆盖已有文件。服务端数据库只保存券码的 SHA-256 摘要，无法找回明文；请在生成时妥善保存并通过可信渠道发放。每张有效券码仅能抽奖一次。查看奖项库存与记录统计：

```bash
docker compose -f deploy/lottery.compose.yml run --rm lottery-api python app.py report
```

## 抽奖规则

- 持有效且未使用的兑奖码即可抽奖，不设固定的抽奖日期范围；同一兑奖码只能使用一次。
- 一等奖、二等奖页面展示概率为 0%；三等奖 5%（最多 6 名）、四等奖 10%（最多 10 名）、五等奖 25%（最多 20 名），谢谢惠顾初始 60%，综合中奖率 40%。
- 奖项名额用完后，该奖项概率转给“谢谢惠顾”；其他奖项概率不变。名额是上限，随机结果不保证每个奖项都会抽满。
- 抽奖结果和查询弹窗显示实际抽奖时间。原抽奖码同时是中奖后的兑换核验码；客服可用页面查询真实结果。查询系统不记录客服是否已完成兑奖，客服仍需自行登记已兑奖的码，避免重复发放。
- 活动规则及奖品发放最终解释权归椰椰电竞所有。

本地浏览器演示页、100 张测试码和演示生成器已移除。部署构建上下文仅包含 API 源码和依赖清单；本机残留的忽略数据文件不进入 API 镜像。不要把 `lottery_backend/data` 内容发布到网页目录。
