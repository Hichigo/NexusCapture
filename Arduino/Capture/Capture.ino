#include "I2Cdev.h"
#include "MPU6050.h"

#define T_OUT 100

MPU6050 accel;

unsigned long int t_next;

void setup() {
    Serial.begin(115200);
    accel.initialize();
    Serial.println(accel.testConnection() ? 1 : 0);
}

void loop() {
    long int t = millis();
    
    if( t_next < t ){
        int16_t ax_raw, ay_raw, az_raw, gx_raw, gy_raw, gz_raw;

        t_next = t + T_OUT;
        accel.getMotion6(&ax_raw, &ay_raw, &az_raw, &gx_raw, &gy_raw, &gz_raw);
        String str = ax_raw + String("|") + ay_raw + String("|") + az_raw + String("|") + gx_raw + String("|") + gy_raw + String("|") + gz_raw;
        Serial.println(str);
    }
}