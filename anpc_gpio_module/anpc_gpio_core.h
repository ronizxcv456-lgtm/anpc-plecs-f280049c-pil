#ifndef ANPC_GPIO_CORE_H
#define ANPC_GPIO_CORE_H
#include <stdint.h>

/* Logical bit order: AT2, AT3, BT2, BT3, CT2, CT3. */
typedef struct {
    uint16_t active;
    uint16_t positive;
    uint16_t pending;
    uint16_t gates;
    uint16_t ready;
    uint16_t enabled;
} AnpcGpioState;

static void anpc_core_reset(volatile AnpcGpioState *s)
{
    s->active = s->positive = s->pending = s->gates = 0U;
    s->ready = s->enabled = 0U;
}

/* Return the phases whose old gate must be switched off now.
 * Opening a new gate is exclusively the job of anpc_core_service(). */
static uint16_t anpc_core_request(volatile AnpcGpioState *s,
                                  uint16_t positive, uint16_t enable)
{
    uint16_t i, changed = 0U;
    if (!enable) {
        anpc_core_reset(s);
        return 0U;
    }
    s->enabled = 1U;
    positive &= 7U;
    for (i = 0U; i < 3U; ++i) {
        uint16_t phase = (uint16_t)(1U << i);
        if (!(s->active & phase) || ((s->positive ^ positive) & phase)) {
            s->gates &= (uint16_t)~(3U << (2U * i));
            s->active |= phase;
            s->positive = (uint16_t)((s->positive & ~phase) | (positive & phase));
            s->pending |= phase;
            changed |= phase;
        }
    }
    return changed;
}

/* Call only after the one-shot delay has elapsed. Normal commutation
 * keeps ready latched; it does not blank the other phases' PWM. */
static void anpc_core_service(volatile AnpcGpioState *s)
{
    uint16_t i;
    if (!s->enabled) return;
    for (i = 0U; i < 3U; ++i) {
        uint16_t phase = (uint16_t)(1U << i);
        if (s->pending & phase) {
            uint16_t shift = (uint16_t)(2U * i + ((s->positive & phase) ? 0U : 1U));
            s->gates &= (uint16_t)~(3U << (2U * i));
            s->gates |= (uint16_t)(1U << shift);
        }
    }
    s->pending = 0U;
    if (s->active == 7U) s->ready = 1U;
}
#endif
