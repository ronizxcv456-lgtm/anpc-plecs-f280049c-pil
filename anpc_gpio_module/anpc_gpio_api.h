#ifndef ANPC_GPIO_API_H
#define ANPC_GPIO_API_H
#include <stdint.h>
uint16_t ANPC_GPIO_update(uint16_t positive, uint16_t enable);
void ANPC_GPIO_configure(void);
void ANPC_GPIO_reset(void);
void ANPC_GPIO_enterPil(void);
void ANPC_GPIO_leavePil(void);
void ANPC_GPIO_stopHardware(void);
#endif
