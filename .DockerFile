FROM node:18-alpine

WORKDIR /app
COPY . .

RUN npm i -g http-server

ENV PORT=8080
EXPOSE 8080

# -c-1 关闭缓存；如需缓存可去掉
CMD ["sh","-c","http-server -p ${PORT} -c-1 ."]