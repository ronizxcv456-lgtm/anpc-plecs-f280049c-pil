"""Build the drag-and-drop PLECS target block using the installed schema."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def param(key, value, indent="        "):
    return (f'{indent}Parameter {{\n{indent}  Variable {q(key)}\n'
            f'{indent}  Value {q(value)}\n{indent}  Show off\n{indent}}}\n')


def comp(kind, name, position, parameters=(), body="", direction="right"):
    result = (f'        Component {{\n          Type {kind}\n          Name {q(name)}\n'
              f'          Show on\n          Position [{position}]\n'
              f'          Direction {direction}\n          Flipped off\n          LabelPosition south\n')
    for key, value in parameters:
        result += param(key, value, "          ")
    return result + body + "        }\n"


def connection(src, st, dst, dt):
    return (f'        Connection {{\n          Type Signal\n          SrcComponent {q(src)}\n'
            f'          SrcTerminal {st}\n          DstComponent {q(dst)}\n'
            f'          DstTerminal {dt}\n        }}\n')


path = ROOT.as_posix()
decl = (f'#include <float.h>\n#include "{path}/anpc_gpio_core.h"\n'
        'static AnpcGpioState lf_state;\nstatic double lf_deadline, lf_last_tick;\n'
        'static unsigned short lf_ready_held;\n')
start = ('anpc_core_reset(&lf_state);\nlf_deadline = DBL_MAX;\n'
         'lf_last_tick = -DBL_MAX;\nlf_ready_held = 0U;\nNextSampleHit = DBL_MAX;\n')
script_params = [
    ('NumInputs', '[3 1]'), ('NumOutputs', '[6 1]'), ('NumContStates', '0'),
    ('NumDiscStates', '0'), ('NumZCSignals', '0'), ('DirectFeedthrough', '[1 1]'),
    ('Ts', '[0 -1; -2 0; UpdateTs 0]'), ('Parameters', 'DeadTime, UpdateTs'),
    ('LangStandard', '2'), ('GnuExtensions', '2'), ('RuntimeCheck', '2'),
    ('Declarations', decl), ('StartFcn', start),
    ('OutputFcn', (ROOT / 'sim_output.c').read_text(encoding='utf-8')),
    ('UpdateFcn', ''), ('DerivativeFcn', ''), ('TerminateFcn', ''),
    ('StoreCustomStateFcn', ''), ('RestoreCustomStateFcn', '')
]
inputs = [('Index', '1'), ('Width', '3'), ('InitialOutput', '[]'),
          ('HasDirectFeedthrough', '2'), ('DataType', '1')]
enable = [('Index', '2'), ('Width', '1'), ('InitialOutput', '[]'),
          ('HasDirectFeedthrough', '2'), ('DataType', '1')]
schematic = ('      Schematic {\n        Location [250, 180; 1050, 550]\n'
             '        ZoomFactor 1\n        SliderPosition [0, 0]\n        ShowBrowser off\n')
schematic += comp('Input', 'Dir', '70, 100', inputs)
schematic += comp('Input', 'En', '70, 180', enable)
schematic += comp('CScript', 'Peripheral model', '240, 130', script_params, direction='up')
schematic += comp('DataType', 'GateType', '355, 100', [('DataType', '4'), ('DataTypeOverflowMode', '1')])
schematic += comp('DataType', 'ReadyType', '355, 180', [('DataType', '4'), ('DataTypeOverflowMode', '1')])
schematic += comp('TargetOutput', '1', '475, 100', [('Width', '6')])
schematic += comp('Output', 'Ready', '475, 180', [('Index', '3'), ('Width', '1')])
schematic += connection('Dir', 1, 'Peripheral model', 1)
schematic += connection('En', 1, 'Peripheral model', 2)
schematic += connection('Peripheral model', 3, 'GateType', 1)
schematic += connection('Peripheral model', 4, 'ReadyType', 1)
schematic += connection('GateType', 2, '1', 1)
schematic += connection('ReadyType', 2, 'Ready', 1)
schematic += '      }\n'

code = ("local block = Target.Coder.CreateTargetBlock('anpc_gpio')\n"
        "return block:getDirectFeedthroughCode()\n")
component = ('    Component {\n      Type TargetCode\n      Name "ANPC_LF_GPIO"\n'
             '      Show on\n      Position [240, 170]\n      Direction up\n'
             '      Flipped off\n      LabelPosition south\n      Frame [-95, -55; 95, 55]\n'
             '      TargetPortIndices "1"\n      SampleTime "0"\n      EnforceBaseTask "2"\n'
             '      CodeFcnLang "2"\n')
component += f'      CodeFcn {q(code)}\n'
component += ('      MaskType "ANPC LF GPIO"\n'
              '      MaskDescription "Three-phase GPIO commutation: turn off, one-shot CPU Timer2 delay, turn on. Input order A B C. Physical GPIOs are disabled during PIL."\n'
              '      MaskDisplayLang "2"\n')
display = "Icon:text(0, 0, 'GPIO\\nTimer2');"
component += f'      MaskDisplay {q(display)}\n'
component += '      MaskIconFrame on\n      MaskIconOpaque off\n      MaskIconRotates off\n'
for key, prompt, value in [
    ('Gpio', 'GPIO pins [AS2 AS3 BS2 BS3 CS2 CS3]', '[12 13 14 15 16 17]'),
    ('DeadTime', 'One-shot timer delay [s]', '1e-6'),
    ('UpdateTs', 'Controller update period [s]', 'Ts_controller'),
    ('ModuleDir', 'Local module folder', "'" + path + "'")
]:
    component += (f'      Parameter {{\n        Variable {q(key)}\n        Prompt {q(prompt)}\n'
                  f'        Type FreeText\n        Value {q(value)}\n'
                  '        Show off\n        Tunable off\n      }\n')
for kind, pos, direction in [('Input', '-95, -30', 'left'),
                             ('Input', '-95, 30', 'left'),
                             ('Output', '95, 0', 'right')]:
    component += (f'      Terminal {{\n        Type {kind}\n        Position [{pos}]\n'
                  f'        Direction {direction}\n      }}\n')
component += schematic + '    }\n'

text = ('Plecs {\n  Name "ANPC_GPIO_Module_v2"\n  Version "5.0"\n'
        '  CircuitModel "ContStateSpace"\n  StartTime "0"\n  TimeSpan "0.1"\n'
        '  Solver "dopri"\n  MaxStep "1e-7"\n  InitStep "-1"\n'
        '  InitializationCommands "Ts_controller = 50e-6;"\n'
        '  CodeGenTarget "Generic"\n  Schematic {\n'
        '    Location [350, 180; 1120, 730]\n    ZoomFactor 1\n'
        '    SliderPosition [0, 0]\n    ShowBrowser off\n' + component + '  }\n}\n')
out = ROOT / 'ANPC_GPIO_Module_v2.plecs'
out.write_text(text, encoding='utf-8')
print(out)
