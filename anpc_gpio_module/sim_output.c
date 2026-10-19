if (IsSampleHit(0)) {
    unsigned short positive = 0U;
    unsigned short enable = (InputSignal(1, 0) != 0.0);
    unsigned short changed;
    int i;
    for (i = 0; i < 3; ++i)
        if (InputSignal(0, i) != 0.0) positive |= (unsigned short)(1U << i);
    changed = anpc_core_request(&lf_state, positive, enable);
    if (!enable) {
        lf_deadline = DBL_MAX;
        lf_ready_held = 0U;
        NextSampleHit = DBL_MAX;
    } else if (changed) {
        lf_deadline = CurrentTime + ParamRealData(0, 0);
        NextSampleHit = lf_deadline;
    }
}
if (IsSampleHit(1) && CurrentTime >= lf_deadline) {
    anpc_core_service(&lf_state);
    lf_deadline = DBL_MAX;
    NextSampleHit = DBL_MAX;
}
/* Match the DSP: release PWM only at a controller tick after initial
 * low-frequency commutation is complete. Keep Ready during later changes. */
if (IsSampleHit(2) && CurrentTime != lf_last_tick) {
    lf_ready_held = lf_state.ready;
    lf_last_tick = CurrentTime;
}
{
    int i;
    for (i = 0; i < 6; ++i)
        OutputSignal(0, i) = (lf_state.gates & (1U << i)) ? 1.0 : 0.0;
    OutputSignal(1, 0) = lf_state.enabled ? lf_ready_held : 0.0;
}
