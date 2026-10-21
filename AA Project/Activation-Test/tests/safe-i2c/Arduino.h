#pragma once
#include <stdint.h>
#include <stddef.h>
#define A4 18
#define A5 19
#define INPUT 0
#define OUTPUT 1
#define LOW 0
#define HIGH 1
void digitalWrite(uint8_t,uint8_t);
void pinMode(uint8_t,uint8_t);
int analogRead(uint8_t);
uint32_t micros();
void delay(unsigned long);
void delayMicroseconds(unsigned int);
