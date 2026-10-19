# 运行步骤

模型来自2026年10月16日保存的`npc_converter.plecs`。仓库中的模板保留了电路与控制参数，使用前需要填入本机路径。

## 软件与硬件

已使用的软件版本如下。其他版本需要重新核对目标支持包接口。官网下载页可能提供更新版本，安装时应同时检查PLECS与TSP的兼容要求。

| 项目 | 版本或型号 |
| --- | --- |
| PLECS Standalone | 5.0.1 |
| PLECS Coder | 与当前PLECS安装匹配的许可 |
| TI C2000 Target Support Package | 2.2.3 |
| TI C2000编译器 | 22.6.1.LTS |
| DSP | TMS320F280049C |
| Python | 3.10或更高，仅用于准备本地路径 |

Code Composer Studio可用于检查和调试生成工程。烧录与串口连接按所用开发板配置，不能直接套用其他计算机的串口号。

## 模型与模块文件

仓库文件关系如下：

```text
models/npc_converter.plecs        # 路径模板
scripts/prepare_project.py       # 生成本机可打开的模型
build/npc_converter.plecs        # 本机副本，不纳入Git
anpc_gpio_module/
    anpc_gpio.lua
    anpc_gpio_api.h
    anpc_gpio_core.h
    anpc_gpio_hal.inc
    sim_output.c
    make_module.py
```

`make_module.py`用于生成可单独使用的GPIO模块；打开已嵌入该模块的主模型不必先运行它。代码生成仍需Lua文件和对应的C头文件、HAL模板。

## 准备本机模型

在仓库根目录执行：

```powershell
py scripts/prepare_project.py
```

如果Python通过`python`命令启动，可改用`python scripts/prepare_project.py`。无需安装额外Python包。

脚本生成`build/npc_converter.plecs`，并填入本机模块目录、C-Script头文件、代码生成输出目录和CCS工程目录。最后一处路径保存在序列化目标设置中，脚本同时更新它的字符串长度信息。

然后在PLECS中打开`build/npc_converter.plecs`。代码生成输出指向`build/codegen`；CCS路径指向`build/ccs_project/280049/cg`。这一步没有运行仿真或访问开发板。

如果本机副本已存在，脚本会停止，避免覆盖你在PLECS中保存的编辑。只有确认可以替换时，才执行：

```powershell
py scripts/prepare_project.py --force
```

`models/npc_converter.plecs`保留路径占位符，不能直接用于仿真。移动或重新克隆仓库后，需要重新准备本机副本。

## 配置自定义TSP入口

代码生成需要TSP的`lua/blocks/anpc_gpio.lua`入口，标准TSP安装不自带本项目的目标块。

将仓库`anpc_gpio_module/anpc_gpio.lua`复制到所用TSP安装目录的`lua/blocks`。若已有同名文件，先比较内容；不要覆盖其他项目正在使用的不同版本。脚本不会代为修改TSP安装目录。

该Lua模块通过模型中的ModuleDir读取头文件和HAL模板。路径准备脚本已设置该字段和C-Script头文件位置，无需再把它们改回原工程路径。

升级TSP后，应重新检查该入口和目标块接口。主模型已嵌入GPIO模块；直接打开主模型不需要运行`make_module.py`。

## 核对初始化命令

当前工况对应：

```matlab
DO_DSP_LED = 34;
SCI_DSP = [28,29];
Ts_controller = 50e-6;  % 控制周期，20 kHz
Ts_gate = 1e-6;        % 门极逻辑采样参数
f_pwm = 80000;         % PWM载波频率，80 kHz
Td_pwm = 200e-9;       % PWM死区，200 ns
K_dt = 1;             % 死区补偿系数
I_dt = 0.5;           % 电流过零平滑阈值，A
```

这些注释已经按数值重写。本地保存的模型还留有“1微秒”和“先关闭”等旧注释，判断参数时应以赋值为准。

TOP和BOT的载波频率都应引用`f_pwm`，固定死区都应引用`Td_pwm`。TOP任务设为Underflow、Divider为4，BOT任务触发设为Disabled。

`ANPC_LF_GPIO`中的`DeadTime`为低频换流等待时间，目前为1 µs。修改`Td_pwm`不会自动改变它。

## 离线仿真

打开主模型，在`Control_logic`中选择`Codegen`控制分支。先核对软件依赖、模块路径和参数，再运行仿真。

观察输出相电压、负载电流、上下母线电容电压，以及`LoopMonitor`中的dq量。d轴电压参考约70.7 ms升到200 V。稳态时Vd应接近参考、Vq接近0；ILd和ILq应分别跟随各自参考。

## 构建与PIL

在Controller中完成代码生成和编译，确认没有构建错误，再通过开发板对应的连接方式下载程序。随后切换到PIL分支，配置本机串口与信号映射。

更改频率或死区后，PIL必须使用重新生成和下载的程序。仅修改计算机模型中的初始化变量，不会改变DSP里已经下载的固件。

### PIL输入

| 端口 | 宽度 | 顺序 |
| --- | --- | --- |
| Enable | 1 | 外部使能，使用0或1 |
| Feedback | 11 | Voa、Vob、Voc、ILa、ILb、ILc、Ioa、Iob、Ioc、VC1、VC2 |

电压单位V，电流单位A。符号列表可能按字典序显示1、10、11、2，应按数值序号选择。

### PIL输出

| 端口 | 宽度 | 对应探针 |
| --- | --- | --- |
| D_TOP | 3 | `TopDuty_1`至`TopDuty_3` |
| D_BOT | 3 | `BotDuty_1`至`BotDuty_3` |
| Direction | 3 | `PhaseDir_1`至`PhaseDir_3` |
| Run16 | 1 | `RunState_1` |
| LoopMonitor | 6 | Vd、Vq、ILd、ILq、ILd_ref、ILq_ref |

输出合计16个标量。Run16应读取`RunState_1`，其中包含母线运行许可；直接使用`Enable_1`会绕过这项条件。

GPIO12至17按AT2、AT3、BT2、BT3、CT2、CT3顺序分配。高频PWM资源TOP为[1 3 5]，BOT为[2 4 6]。实际接线须按开发板引脚复用和功率级标号逐一确认。

## 常见问题

| 现象 | 优先检查 |
| --- | --- |
| 找不到`anpc_gpio`目标块 | TSP的Lua入口与模块版本 |
| C-Script找不到头文件 | Peripheral model的Declarations路径 |
| 改参数后PIL结果没有变化 | 是否重新生成、下载，PIL是否连接正确程序 |
| 控制任务周期不匹配 | TOP触发分频是否与`Ts_controller`一致 |
| 直流母线有电压但不运行 | Enable、Vdc大于50 V条件及`RunState_1`映射 |
| ILq不为0 | 是否包含滤波电容无功电流，是否跟随ILq_ref |
