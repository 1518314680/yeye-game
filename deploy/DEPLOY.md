# 椰椰电竞 Nginx 部署

沿用现有容器和挂载路径：`yeye-nginx`、宿主机端口 `9999`、Nginx 配置目录 `/home/ubuntu/yeye/nginx`、公开网页目录 `/home/ubuntu/yeye/nginx/html`。抽奖 API 作为独立容器运行，不再启动第二个 Nginx。

## 发布静态网页

将公开网页文件（包括 `lottery.html`、其他游戏页面、CSS、图片和资源目录）放到 `/home/ubuntu/yeye/nginx/html`。不要把整个仓库复制到公开目录；尤其不要放入 `lottery_backend`、`deploy`、`.git` 或任何兑奖码/数据库文件。

将 `deploy/nginx/yeye.conf` 的抽奖 API 配置合并到宿主机的 `/home/ubuntu/yeye/nginx/yeye.conf`。如果该文件含有自己的首页或路由规则，保留原规则，只合并 `limit_req_zone`、Docker DNS 设置、三个 `/api/lottery/*` 路由、`/lottery.html` 缓存规则和源码目录拒绝规则。不要另加第二个监听 9999 的 `server` 配置。

## 让现有 Nginx 接入抽奖网络

首次部署时创建共享网络：

```bash
docker network create yeye-lottery
```

现有 `yeye-nginx` 已在运行时，将它接入网络一次即可：

```bash
docker network connect yeye-lottery yeye-nginx
```

如果是新建 Nginx 容器，则在原 `docker run` 命令中加入 `--network yeye-lottery`。原有 9999 端口和两个挂载路径保持不变。

## 启动抽奖 API

在服务器上的项目仓库根目录执行（该源码目录应在公开网页目录之外）：

```bash
docker compose -f deploy/lottery.compose.yml up -d --build
```

Compose 文件只启动 `lottery-api`，复用上面的 `yeye-lottery` 网络；不会启动或占用新的 Nginx 端口。数据库保存在 Docker 卷 `yeye_lottery_data` 中。API 的 8000 端口只在 Docker 网络内可访问，不要额外映射到公网。

API 启动后检查并重启现有 Nginx，使其加载新配置：

```bash
docker exec yeye-nginx nginx -t
docker restart yeye-nginx
```

改网页文件只需刷新浏览器；改 Nginx 配置后先运行 `nginx -t`，通过后再重启容器。

## 验证

```bash
curl -i http://127.0.0.1:9999/api/lottery/prizes
```

然后访问 `http://<服务器IP>:9999/lottery.html`。放行宿主机 9999 端口；生产使用时应在站点前配置 HTTPS。
