/* Generated into Controller_hal.c by the local target block.
 * Timer1 belongs to the PLECS dispatcher. This block owns CPU Timer2. */
static volatile AnpcGpioState AnpcGpioStateData;
static volatile uint16_t AnpcGpioPilMode = 0U;
static uint16_t AnpcGpioPilPreviousEnable = 0U;
static const uint32_t AnpcGpioPhasePins[3] = {@PHASE_MASKS@};
static const uint32_t AnpcGpioPinBits[6] = {@PIN_BITS@};

static void ANPC_GPIO_stopTimer(void)
{
    CpuTimer2Regs.TCR.bit.TSS = 1;
    CpuTimer2Regs.TCR.bit.TIF = 1;
    IFR &= (uint16_t)~M_INT14;
}

void ANPC_GPIO_stopHardware(void)
{
    ANPC_GPIO_stopTimer();
    GpioDataRegs.GPACLEAR.all = @ALL_PINS@;
}

void ANPC_GPIO_reset(void)
{
    uint16_t saved = IER;
    IER &= (uint16_t)~M_INT14;
    ANPC_GPIO_stopHardware();
    anpc_core_reset(&AnpcGpioStateData);
    AnpcGpioPilPreviousEnable = 0U;
    IER = (uint16_t)((IER & ~M_INT14) | (saved & M_INT14));
}

void ANPC_GPIO_enterPil(void)
{
    AnpcGpioPilMode = 1U;
    ANPC_GPIO_reset();
}

void ANPC_GPIO_leavePil(void)
{
    ANPC_GPIO_reset();
    AnpcGpioPilMode = 0U;
}

static __interrupt void ANPC_GPIO_timer2Interrupt(void)
{
    uint16_t i;
    uint32_t on = 0UL;
    ANPC_GPIO_stopTimer();
    if (AnpcGpioPilMode || !AnpcGpioStateData.enabled) {
        GpioDataRegs.GPACLEAR.all = @ALL_PINS@;
        return;
    }
    anpc_core_service(&AnpcGpioStateData);
    for (i = 0U; i < 6U; ++i) {
        if (AnpcGpioStateData.gates & (1U << i)) on |= AnpcGpioPinBits[i];
    }
    GpioDataRegs.GPASET.all = on;
}

void ANPC_GPIO_configure(void)
{
    ANPC_GPIO_stopHardware();
    EALLOW;
    CpuSysRegs.TMR2CLKCTL.bit.TMR2CLKSRCSEL = 0U;
    CpuSysRegs.TMR2CLKCTL.bit.TMR2CLKPRESCALE = 0U;
    PieVectTable.TIMER2_INT = &ANPC_GPIO_timer2Interrupt;
    EDIS;
    CpuTimer2Regs.TPR.all = 0U;
    CpuTimer2Regs.TPRH.all = 0U;
    CpuTimer2Regs.PRD.all = @TIMER_PRD@;
    CpuTimer2Regs.TCR.all = 0x4010U; /* interrupt enabled, timer stopped */
    CpuTimer2Regs.TCR.bit.TSS = 1U;
    CpuTimer2Regs.TCR.bit.TRB = 1U;
    CpuTimer2Regs.TCR.bit.TIF = 1U;
    ANPC_GPIO_reset();
    IER |= M_INT14;
}

uint16_t ANPC_GPIO_update(uint16_t positive, uint16_t enable)
{
    uint16_t saved, changed, i, result;
    uint32_t off = 0UL;
    enable = enable ? 1U : 0U;
    if (AnpcGpioPilMode) {
        /* The target-block output override supplies the peripheral model's
         * Ready signal during PIL. No physical low-frequency gate is opened. */
        ANPC_GPIO_stopHardware();
        result = (uint16_t)(enable && AnpcGpioPilPreviousEnable);
        AnpcGpioPilPreviousEnable = enable;
        return result;
    }
    saved = IER;
    IER &= (uint16_t)~M_INT14;
    changed = anpc_core_request(&AnpcGpioStateData, positive, enable);
    if (!enable) {
        ANPC_GPIO_stopHardware();
    } else if (changed) {
        ANPC_GPIO_stopTimer();
        for (i = 0U; i < 3U; ++i) {
            if (changed & (1U << i)) off |= AnpcGpioPhasePins[i];
        }
        GpioDataRegs.GPACLEAR.all = off;
        CpuTimer2Regs.TCR.bit.TRB = 1U;
        CpuTimer2Regs.TCR.bit.TSS = 0U;
    }
    result = (uint16_t)(enable && AnpcGpioStateData.ready);
    IER = (uint16_t)((IER & ~M_INT14) | (saved & M_INT14));
    return result;
}
