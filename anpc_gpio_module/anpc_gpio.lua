local U = require('common.utils')
local M = {}
local count = {}

local function readFile(path)
    local f, err = io.open(path, 'rb')
    if not f then error(err) end
    local s = f:read('*a')
    f:close()
    return s
end

function M.getBlock(globals, cpu)
    local B = require('common.block').getBlock(globals, cpu)
    count[cpu] = (count[cpu] or 0) + 1
    if count[cpu] ~= 1 then U.error('Use exactly one ANPC LF GPIO block per CPU: it owns CPU Timer2.') end
    B.instance = 0

    function B:checkMaskParameters()
        if not self:targetMatches({'28004x'}) then U.error('This GPIO block is for TI F28004x only.') end
        local pins = Block.Mask.Gpio
        if type(pins) ~= 'table' or #pins ~= 6 then U.error('Gpio must be a six-element vector: AT2 AT3 BT2 BT3 CT2 CT3.') end
        local used = {}
        self.pins = {}
        for i, pin in ipairs(pins) do
            if type(pin) ~= 'number' or pin ~= math.floor(pin) or pin < 0 or pin > 31 or used[pin] then
                U.error('GPIO pins must be unique integers in bank A, 0 through 31.')
            end
            used[pin] = true
            self.pins[i] = pin
        end
        self.delay = Block.Mask.DeadTime
        self.updateTs = Block.Mask.UpdateTs
        if type(self.delay) ~= 'number' or self.delay <= 0 or self.delay >= self.updateTs then
            U.error('DeadTime must be positive and smaller than UpdateTs.')
        end
        self.dir = Block.Mask.ModuleDir:gsub('\\', '/'):gsub('/$', '')
        self.ticks = math.ceil(self.delay * globals.target.getCleanSysClkHz())
        if self.ticks < 2 or self.ticks > 4294967295 then U.error('Invalid CPU Timer2 period.') end
    end

    function B:p_getDirectFeedthroughCode()
        if #Block.InputSignal[1] ~= 3 or #Block.InputSignal[2] ~= 1 then
            U.error('Direction must have width 3 and Enable must have width 1.')
        end
        if math.abs(Block.Task.SampleTime[1] - self.updateTs) > 1e-12 then
            U.error('Assign this block to the base task, with UpdateTs equal to its sample time.')
        end
        local req = ResourceList:new()
        for _, pin in ipairs(self.pins) do
            local dout = self:makeBlock('dout', self.cpu)
            dout:createImplicit(pin, {opt_outputType = 'PUSH_PULL'}, req)
        end

        local recipe = {
            Include = StringList:new(), Declarations = U.CodeLines:new(),
            InitCode = U.CodeLines:new(), OutputCode = U.CodeLines:new(),
            Require = req, UserData = {bid = self:getId()}
        }
        recipe.Include:append(self.dir .. '/anpc_gpio_api.h')
        recipe.InitCode:append('ANPC_GPIO_reset();')
        local out = Block:OutputSignal()
        local d = Block.InputSignal[1]
        recipe.OutputCode:append(string.format(
            '%s = ANPC_GPIO_update((uint16_t)((%s != 0) | ((%s != 0) << 1) | ((%s != 0) << 2)), (uint16_t)(%s != 0));',
            out[1][1], d[1], d[2], d[3], Block.InputSignal[2][1]))

        local pil = self:getBlockInstance('pil')
        if not pil then
            pil = self:makeBlock('pil', self.cpu)
            pil:createImplicit(recipe)
        end
        local previous = pil.getTargetSpecificCallbackCode
        pil.getTargetSpecificCallbackCode = function(obj, c)
            local r = previous(obj, c)
            c.Include:append(self.dir .. '/anpc_gpio_api.h')
            r.disableActuationCode = r.disableActuationCode .. '\nANPC_GPIO_enterPil();'
            r.enableActuationCode = r.enableActuationCode .. '\nANPC_GPIO_leavePil();'
            r.stopTimersCode = r.stopTimersCode .. '\nANPC_GPIO_stopHardware();'
            return r
        end
        return recipe
    end

    function B:finalize(c)
        if self.finalized then return end
        c.Include:append(self.dir .. '/anpc_gpio_api.h')
        c.Include:append(self.dir .. '/anpc_gpio_core.h')
        local bits, phases, all = {}, {}, 0
        for i, pin in ipairs(self.pins) do
            local bit = 2 ^ pin
            all = all + bit
            bits[i] = string.format('0x%08XUL', bit)
        end
        for i = 1, 3 do
            phases[i] = string.format('0x%08XUL', 2 ^ self.pins[2*i-1] + 2 ^ self.pins[2*i])
        end
        local code = readFile(self.dir .. '/anpc_gpio_hal.inc')
        local substitutions = {
            PHASE_MASKS = table.concat(phases, ', '), PIN_BITS = table.concat(bits, ', '),
            ALL_PINS = string.format('0x%08XUL', all), TIMER_PRD = string.format('%dUL', self.ticks - 1)
        }
        code = code:gsub('@([A-Z_]+)@', substitutions)
        c.Declarations:append(code)
        c.PostInitCode:append('ANPC_GPIO_configure();')
        self.finalized = true
    end
    return B
end
return M
