# 三相ANPC逆变器 PLECS与F280049C PIL

Three-phase ANPC inverter model and processor-in-the-loop control for the TI F280049C.

这个项目用于三相ANPC逆变器的控制仿真和DSP处理器在环验证。控制器采用dq电压外环与电感电流内环，包含负载前馈、交叉耦合补偿、矢量限幅、死区补偿和中点电压平衡。

当前工况为400 V直流母线、200 V相电压峰值参考、50 Hz输出，每相负载50 Ω。按正弦参考换算，相电压约141.4 V RMS，三相负载功率约1.2 kW。80 kHz指PWM载波频率；控制算法每50 µs运行一次，即20 kHz。

## 仓库状态

主模型取自2026年10月16日保存的最终版本。仓库包含[模型模板](models/npc_converter.plecs)、自定义GPIO模块和[路径准备脚本](scripts/prepare_project.py)。模板只替换了4处本机路径，电路、控制算法与参数保持原样；来源校验见[文件清单](docs/source-manifest.json)。

先在仓库目录运行下面的命令，再用PLECS打开生成的`build/npc_converter.plecs`。不要直接运行含路径占位符的模板。

```powershell
py scripts/prepare_project.py
```

脚本需要Python 3.10或更高版本，使用标准库。它只生成本机模型副本，不安装TSP、不编译、不烧录。TSP的自定义Lua入口按[运行步骤](docs/getting-started.md)配置。

## 双机并联下垂控制

新增[双ANPC并联模型](models/anpc_parallel_droop.plecs)，包含两套P–f、Q–V下垂控制、虚拟阻抗和2 s负载阶跃，用于观察电流分配、环流及两机频率变化。模型说明与截图见[并联下垂控制](docs/parallel-droop.md)，完整截图保留在[ANPC下垂 Word原稿](docs/ANPC下垂.docx)中。

```powershell
py scripts/prepare_project.py --model anpc_parallel_droop
```

然后打开`build/anpc_parallel_droop.plecs`。两套控制器的本机路径分别填入，代码生成目录互相独立。未指定`--model`时仍准备原单机模型。

## 单机PIL记录

已核对2026年10月16日16:10生成的80 kHz、200 ns死区代码，ELF于16:11生成。作者提供了配置步骤、PIL仿真结果和逻辑分析仪截图，见[配置手册与仿真结果](docs/ANPC.docx)。原始波形数据及逐项测量记录尚未收录。

## 文档

- [并联下垂控制](docs/parallel-droop.md)：模型准备、下垂参数、测量位置与作者提供的波形。
- [配置手册与仿真结果 Word原稿](docs/ANPC.docx)：作者的配置截图、操作记录和仿真波形，按原文件收录；技术校核见下方验证记录。
- [运行步骤](docs/getting-started.md)：软件依赖、模块路径、构建与PIL接口。
- [控制器说明](docs/controller.md)：模块作用、公式、PI参数和PWM时序。
- [验证记录](docs/validation.md)：已完成的验证、当前参数差异及下一次复测内容。
- [第三方说明](THIRD_PARTY_NOTICES.md)：依赖、参考资料和许可范围。

## 当前参数

| 参数 | 数值 |
| --- | --- |
| DSP | TI TMS320F280049C |
| 直流母线 | 400 V |
| 输出频率 | 50 Hz |
| 输出相电压参考 | 峰值200 V，正弦换算约141.4 V RMS |
| 输出线电压参考 | 平衡正弦换算约244.9 V RMS |
| 负载 | 三相星形，每相50 Ω，参考电压下约1.2 kW总负载功率 |
| 滤波电感 | 每相3 mH |
| 滤波电容 | 每相5 µF，支路串联5 Ω阻尼电阻 |
| 直流电容 | 上下各1 mF，初值分别205 V和195 V |
| `f_pwm` | `80000` Hz |
| `Ts_controller` | `50e-6` s |
| `Td_pwm` | `200e-9` s |
| `K_dt` | `1` |
| `I_dt` | `0.5` A |
| 电流参考矢量上限 | 8 A，dq幅值 |
| PWM任务触发 | TOP为Underflow、Divider为4；BOT为Disabled |

这里的1.2 kW由电压参考和负载电阻计算，未计入滤波支路及变换器损耗，也不是实测功率。它与TI TIDA-010210参考硬件的11 kW规格不同。

## 参数需要注意的地方

200 ns死区在80 kHz下占载波周期的1.6%。按模型中的补偿公式，`DT_Gain = K_dt*Td_pwm*f_pwm = 0.016`。

磁盘模型的`VoltageLimitGain`目前是`0.9/sqrt(3)`。如果要为补偿预留幅值裕量，建议表达式为`(0.9-abs(K_dt)*Td_pwm*f_pwm)/sqrt(3)`，对应约0.510378。这项建议尚未应用到保存的模型，详见[控制器说明](docs/controller.md#电压矢量限幅与补偿裕量)。

PWM死区与低频GPIO换流间隔分别设置。`Td_pwm`现在为200 ns，`ANPC_LF_GPIO`模块的`DeadTime`仍为1 µs；`Ts_gate`也是独立参数。

## 运行范围

PIL中，DSP运行控制算法，计算机中的PLECS功率级模型提供反馈。该结果不能证明真实ADC采样、PWM装载延迟和功率器件换流时序已完成验证。

接入实际功率级还需要落实ADC标定、门极对应、执行时间测量和独立硬件故障关断。8 A矢量限幅是电流参考约束。

## 许可

仓库原创内容采用[MIT许可证](LICENSE)。PLECS、TI开发工具及其他第三方内容保留各自的许可。运行模型和生成代码需要用户自行安装相应软件及许可。
