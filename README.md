# RecToForm
1. 本项目基于多模态LLM(视觉模型)批量分析发票文件，提取发票中的所有信息并填写Excel表格
2. 提供两种填写模式：全字段匹配填写和自定义模板填写。用户可在线编辑表格，调整表头和数据列，并支持下载编辑后的Excel文件
3. 支持阿里云百炼官方接口、本地私有化模型部署，用户可根据需求选择不同的LLM提供商
4. 后端采用FastAPI框架，前端使用React，部署方式支持Docker和本地环境配置
5. 服务端与客户端仓库地址
- 服务端: [RecToForm-backend](https://github.com/YunXi-Zhu0/RecToForm-backend.git)
- 客户端: [RecToForm-frontend](https://github.com/YunXi-Zhu0/RecToForm-frontend.git)

# 一、功能演示
## 1. 全字段匹配填写
- 识别发票中所有信息并返回
- 支持在线表格编辑, 自编辑表头及其对应数据信息; 同时支持一键删除、移动、恢复数据列操作
- 支持编辑后表格下载, 导出为Excel表格文件
![002](./assets/2.gif)

## 2. 自定义模板填写
- 用户可通过编辑`template/`下的配置文件以自定义默认模板(可参考已有模板: `asset_import_v1`、`finance_invoice_v1`)
- 导出表格文件的表头由用户自定义配置文件决定
![001](./assets/1.gif)


# 二、快速启动
## 1. 克隆项目到本地
tips: 由于本项目采用前后端分离架构, 所以本仓库以引用的方式集成了两个`submodule`仓库, 分别存放前端、后端代码, 因此在克隆时需要添加`--recurse-submodules`参数
```bash
git clone --recurse-submodules https://github.com/YunXi-Zhu0/RecToForm.git
```

## 2. 配置 `.env` 环境变量
(1) 拷贝 .env 文件
```bash
cp .env.example .env
```
(2) `.env` 文件字段说明
项目根目录下的 `.env` 会被 `docker-compose.yml` 直接加载，后端服务实际读取逻辑位于 `backend/src/core/config.py`。可参考根目录下的 `.env.example`。

推荐最小配置：

- 若使用阿里云百炼官方接口([阿里百炼 -获取 API Key](https://help.aliyun.com/zh/model-studio/get-api-key?spm=a2c4g.11186623.0.0.53bf172azgVCaY))，只需要重点填写 `QWEN3_VL_PLUS_API_KEY`，并将 `LLM_PROVIDER` 设为 `qwen_official`
- 若使用本地兼容 OpenAI 的视觉模型服务，只需要重点填写 `QWEN3_VL_8B_SSPU_API_URL`，并将 `LLM_PROVIDER` 设为 `qwen_local_openai_compatible`
- 其余字段大多已有默认值，通常无需修改

### 1. API 服务配置

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `API_TITLE` | `string` | `RecToForm API` | 后端接口文档和服务标题展示名称。 |
| `API_PREFIX` | `string` | `/api/v1` | API 路由前缀。前后端联调时一般保持默认值。 |
| `API_HOST` | `string` | `127.0.0.1` | 后端监听地址。本地或 Docker 部署通常建议设为 `0.0.0.0`。 |
| `API_PORT` | `int` | `8080` | 后端监听端口。注意当前根目录 `docker-compose.yml` 中启动命令固定为 `8080`，仅修改 `.env` 不会改变容器实际监听端口。 |
| `API_CORS_ORIGINS` | `string` | `*` | 允许跨域访问的来源列表，多个值用英文逗号分隔，例如 `http://localhost:5173,http://127.0.0.1:5173`。 |

### 2. Redis / RQ 队列配置

这些字段用于异步任务队列与导出文件映射存储。

| 字段 | 类型 | 默认值                    | 说明 |
| --- | --- |------------------------| --- |
| `REDIS_URL` | `string` | `redis://redis:6379/0` | Redis 连接地址，后端 API 和 worker 都依赖它。 |
| `EXPORT_FILE_MAPPING_TTL` | `int` | `86400`                | 导出文件映射关系的过期时间，单位为秒。 |
| `RQ_QUEUE_NAME` | `string` | `invoice_tasks`        | RQ 队列名。注意当前根目录 `docker-compose.yml` 中 worker 命令固定监听 `invoice_tasks`，如果修改此值，还需要同步修改 compose 配置。 |
| `RQ_JOB_TIMEOUT` | `int` | `1800`                 | 单个异步任务超时时间，单位为秒。 |
| `RQ_RESULT_TTL` | `int` | `86400`                | RQ 任务结果保留时间，单位为秒。 |
| `RQ_WORKER_PROCESSES` | `int` | `4`                    | worker 并发进程数。 |

### 3. Workflow 执行限制

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `WORKFLOW_ASYNC_CONCURRENCY` | `int` | `15` | 单批任务内部的异步并发数。 |
| `MAX_UPLOAD_FILES` | `int` | `50` | 单次接口允许上传的最大文件数。 |
| `MAX_FILE_SIZE_MB` | `int` | `10` | 单个上传文件大小上限，单位为 MB。 |

### 4. LLM 提供商选择

| 字段 | 类型 | 默认值 | 说明                                                                  |
| --- | --- | --- |---------------------------------------------------------------------|
| `LLM_PROVIDER` | `string` | `qwen_official` | 当前支持阿里云官方模型 `qwen_official` 和私有部署模型 `qwen_local_openai_compatible`。 |

### 5. `qwen_official` 配置

当 `LLM_PROVIDER=qwen_official` 时，主要使用下面这组配置：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `QWEN3_VL_PLUS_API_KEY` | `string` | 无 | 阿里云百炼兼容接口的 API Key，使用官方服务时必填。 |
| `QWEN3_VL_PLUS_TEMPERATURE` | `float` | `0.7` | 模型采样温度。 |
| `QWEN3_VL_PLUS_MAX_TOKENS` | `int` | `1000` | 模型最大输出 token 数。 |

补充说明：

- 官方接口基础地址已在代码中固定为 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `QWEN3_VL_PLUS_MODEL_NAME` 不从 `.env` 读取，当前代码中固定使用 `qwen3.5-plus`


## 3. 启动服务
### 1. Docker 启动(强力推荐)
```bash
docker compose up --build
```
tips: 若本地环境无`Docker`或者遇到网络问题导致所需镜像文件拉去失败, 可参考如下博客进行配置调整: [Docker安装及配置代理](https://yunxi-zhu.top/posts/linux/2026-04-01-docker%E5%AE%89%E8%A3%85%E5%8F%8A%E9%85%8D%E7%BD%AE%E4%BB%A3%E7%90%86/)

### 2. 本地环境启动
(1) 后端环境配置\
可参考 [RecToForm-backend](https://github.com/YunXi-Zhu0/RecToForm-backend) 其中的`三、快速开始`部分\
(2) 前端环境配置\
可参考 [RecToForm-frontend](https://github.com/YunXi-Zhu0/RecToForm-frontend) 其中的`二、快速启动`部分


# 三、自定义模板用户说明
## 1. 参考已有模板文件
1. 进入 `./backend/template` 目录
2. 首先先参考已有模板文件 `./backend/template/finance_invoice_v1.json`, 及其对应的表格文件 `./backend/template/assets/finance_invoice_template_v1.xlsx`

## 2. 创建新的模板文件
1. 在 `./backend/template` 目录下创建新的模板文件, 例如 `xxx_v1.json`
2. 按如下字段编写`json`文件
```json
{
  "template_id": "abc",
  "template_name": "def",
  "template_version": "v1",
  "mapping_version": "v1",
  "excel_template_path": "assets/xxx_v1.xlsx",
  "recommended_field_ids": [
    "发票号码",
    "发票代码",
    ......
  ],
  "default_extra_instructions": [],
  "default_header_labels": {
    "发票号码": "发票号码",
    "发票代码": "发票代码",
    ......
  },
  "excel_mappings": [
    {
      "field_id": "发票号码",
      "sheet_name": "Sheet1",
      "cell": "A2",
      "write_mode": "overwrite",
      "value_source": "standard",
      "source_key": "发票号码"
    },
    {
      "field_id": "发票代码",
      "sheet_name": "Sheet1",
      "cell": "B2",
      "write_mode": "overwrite",
      "value_source": "standard",
      "source_key": "发票代码"
    },
    ......
  ]
}
```
3. 同时创建对应的`Excel`模板文件, 例如 `assets/xxx_v1.xlsx`, 以供系统填写数据使用（其中: 改文件名需要与json文件中的`excel_template_path`字段一一对应）
4. 最后, 在`./backend/template/index.json`文件中添加新模板的相关信息, 例如:
```json
{
  "templates": [
    {
      "template_id": "abc",
      "template_name": "def",
      "template_version": "v1",
      "mapping_version": "v1",
      "file": "xxx_v1.json"
    }
  ]
}
```
其中的`file`字段的值需要与新建的模板配置文件名一致, 以确保系统能够正确加载新模板文件

## 3. 模板文件字段说明
### 1. `xxx_v1.json`文件
该文件用于定义模板的基础信息、默认表头以及每个字段写入 Excel 的位置和取值来源。可参考 `backend/template/finance_invoice_v1.json` 和 `backend/template/asset_import_v1.json`。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `template_id` | `string` | 是 | 模板唯一标识，例如 `finance_invoice`、`asset_import`。接口与后端通过 `template_id + template_version` 定位模板。 |
| `template_name` | `string` | 是 | 模板展示名称，用于前端列表和详情页显示。 |
| `template_version` | `string` | 是 | 模板版本号，例如 `v1`。同一个 `template_id` 可对应多个版本。 |
| `mapping_version` | `string` | 是 | 字段映射版本号，用于标识当前 Excel 映射配置的版本。当前示例中通常与 `template_version` 保持一致。 |
| `excel_template_path` | `string` | 是 | Excel 模板文件相对路径，路径基准是 `./backend/template` 目录，例如 `assets/finance_invoice_template_v1.xlsx`。 |
| `recommended_field_ids` | `string[]` | 是 | 模板默认导出的字段列表，同时决定导出时的字段顺序。这里列出的每个字段都必须在 `default_header_labels` 和 `excel_mappings` 中存在。 |
| `default_extra_instructions` | `string[]` | 否 | 模板默认追加给模型的补充指令列表。每一项都必须是非空字符串；如果没有额外要求可写空数组 `[]`。 |
| `default_header_labels` | `object` | 是 | 默认表头文案映射，键为 `field_id`，值为实际写入 Excel 表头行的文本。通常键和值一致，也可以按业务需要自定义显示名称。 |
| `excel_mappings` | `object[]` | 是 | 字段写入规则列表，每一项定义一个字段应该写到哪个工作表、哪个单元格，以及值从哪里来。 |

`excel_mappings` 中单个映射项字段说明如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `field_id` | `string` | 是 | 模板字段标识，必须唯一，并且通常需要出现在 `recommended_field_ids` 中。 |
| `sheet_name` | `string` | 是 | Excel 工作表名称，必须和模板文件中的 sheet 名一致，例如 `Sheet1`。 |
| `cell` | `string` | 是 | 数据写入单元格位置，例如 `A2`、`B2`。系统会将对应表头写入它的上一行单元格，例如 `A2` 对应表头 `A1`。 |
| `write_mode` | `string` | 否 | 写入方式，当前模板示例统一使用 `overwrite`；后端当前实现也是直接覆盖目标单元格内容。 |
| `value_source` | `string` | 否 | 值来源。当前后端支持 `standard`、`system`、`user`、`rule`、`literal`。其中 `standard` 表示从标准字段识别结果中取值；其余类型当前都会回退写入 `default_value`，通常用于预留固定值、用户补充值或规则计算值。 |
| `source_key` | `string` | 条件必填 | 当 `value_source` 为 `standard` 时必填，表示对应的标准字段名，例如 `发票号码`、`合计`、`销售方名称`。字段名必须存在于后端标准字段定义中。 |
| `default_value` | `string` | 否 | 默认值。当标准字段缺失，或 `value_source` 不是 `standard` 时，系统会写入该值；如果未填写则默认写空字符串。 |

补充约束：

- `recommended_field_ids` 中的字段顺序，就是最终模板模式导出的列顺序。
- `default_header_labels` 必须覆盖全部 `recommended_field_ids`。
- `excel_mappings` 中至少要包含全部 `recommended_field_ids` 对应的映射项，且 `field_id` 不能重复。
- `source_key` 建议直接复用现有标准字段名称，避免因为字段名不在标准字段集合中而导致模板加载失败。

### 2. `index.json`文件
该文件用于注册模板清单，后端会先读取它，再根据 `template_id` 和 `template_version` 找到对应的模板配置文件。当前结构如下：

```json
{
  "templates": [
    {
      "template_id": "finance_invoice",
      "template_name": "财务系统录入发票字段",
      "template_version": "v1",
      "mapping_version": "v1",
      "file": "finance_invoice_v1.json"
    }
  ]
}
```

字段说明如下：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `templates` | `object[]` | 是 | 模板注册列表，每个元素代表一个可被系统发现的模板版本。 |
| `template_id` | `string` | 是 | 模板唯一标识，需要与对应 `xxx_v1.json` 中的 `template_id` 保持一致。 |
| `template_name` | `string` | 是 | 模板展示名称，需要与对应模板配置保持一致。 |
| `template_version` | `string` | 是 | 模板版本号，需要与对应模板配置保持一致。 |
| `mapping_version` | `string` | 是 | 映射版本号，需要与对应模板配置保持一致。 |
| `file` | `string` | 是 | 模板配置文件名，路径基准是 `./backend/template`，例如 `finance_invoice_v1.json`。注意这里指向的是 JSON 配置文件，不是 Excel 文件。 |

建议：

- 每新增一个模板版本，都在 `templates` 中追加一项注册信息。
- 同一组 `template_id + template_version` 应保持唯一，避免后端命中到错误配置。
- `file` 对应的 JSON 文件中再通过 `excel_template_path` 关联实际 Excel 模板文件。

