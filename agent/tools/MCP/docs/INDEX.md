# 1Panel 开发文档

mcp-1panel 开发参考资源。

## 文件索引

| 文件 | 说明 |
|------|------|
| api-swagger.json | 1Panel API 完整 Swagger 定义（603 个端点） |
| api-manual.html | 1Panel 官方 API 接口文档 |

## API 概览

源文档: api-swagger.json（639KB, 603 endpoints, OAS 2.0）

Base URL: /api/v2

### 模块分布

| 模块 | 端点数 |
|------|--------|
| /websites | 90 |
| /ai | 73 |
| /containers | 67 |
| /core | 63 |
| /hosts | 43 |
| /databases | 42 |
| /files | 40 |
| /toolbox | 39 |
| /runtimes | 31 |
| /apps | 29 |
| /backups | 20 |
| /settings | 19 |
| /cronjobs | 16 |
| /dashboard | 12 |
| /openresty | 9 |
| /groups | 4 |
| /logs | 3 |
| /process | 3 |

### 认证方式

Token = md5("1panel" + API-Key + UnixTimestamp)

请求头: 1Panel-Token + 1Panel-Timestamp

详见 api-manual.html

### 数据结构

Swagger 文档中包含完整的 definitions / schemas，可作为请求参数和响应格式的参考。
