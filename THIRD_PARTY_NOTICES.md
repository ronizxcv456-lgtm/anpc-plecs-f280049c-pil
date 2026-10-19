# 第三方依赖与参考资料

仓库根目录的MIT许可证适用于本项目有权发布的原创内容。外部软件、库、官方示例及其派生部分保留原有许可。

## 软件依赖

| 名称 | 本项目中的用途 | 获取方式 |
| --- | --- | --- |
| PLECS Standalone | 电路建模与仿真 | [Plexim](https://www.plexim.com/products/plecs) |
| PLECS Coder | 从控制模型生成代码 | [Plexim Coder](https://www.plexim.com/products/plecs_coder) |
| TI C2000 Target Support Package | F280049C外设与构建支持 | [Plexim TSP下载](https://www.plexim.com/download/tsp_c2000) |
| TI C2000编译器 | 编译C28x目标程序 | [TI编译器](https://www.ti.com/tool/C2000-CGT) |
| Code Composer Studio | DSP工程检查与调试 | [TI CCS](https://www.ti.com/tool/CCSTUDIO) |

本项目不分发上述软件的安装包、许可文件或整套SDK。用户按各自的软件许可安装依赖。

`anpc_gpio.lua`调用Plexim TSP提供的目标块接口。代码生成过程会引用TSP及TI头文件，新增的项目许可证不替代这些文件自身的许可。

## 技术资料

- Plexim：[三相到旋转坐标系变换](https://docs.plexim.com/plecs/5.0/components-by-category/abc2dq/)。
- Plexim：[离散PID控制器](https://docs.plexim.com/plecs/latest/components-by-category/discretepidcontroller/)。
- Plexim：[离散传递函数](https://docs.plexim.com/plecs/latest/components-by-category/disctransferfcn/)。
- Plexim：[THD模块](https://docs.plexim.com/plecs/latest/components-by-category/thd/)。
- Plexim：[C-Script与外部头文件](https://docs.plexim.com/plecs/5.0/c-scripts/)。
- Texas Instruments：[TIDA-010210 ANPC参考设计](https://www.ti.com/tool/TIDA-010210)。

TI TIDA-010210用于拓扑与高频ANPC设计参考。当前项目按200 V相电压峰值参考和每相50 Ω负载计算，为约1.2 kW负载工况，没有复现其11 kW整机，也不宣称获得TI或Plexim的认证或背书。

## 项目文件与来源

主模型与GPIO模块来自作者指定的最终工程，来源哈希记录在[文件清单](docs/source-manifest.json)。路径准备脚本与测试属于本仓库的辅助代码。

模型含对PLECS与TSP标准库的引用，使用时依赖对应软件安装，仓库未复制整套厂商库。对于后续加入的官方示例派生内容或第三方代码，应保留适用的版权声明、许可文本和来源链接。

自动生成代码需要连同所引用运行库的条款一起确认。当前仓库未加入生成代码、厂商库或固件二进制文件。
