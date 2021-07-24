//
//  modbusRegisters.h
//  Example file with modbus register definitions
//
//  Created by brainelectronics on 24.07.2021
//  Modified on 24.07.2021
//
//  Copyright (c) 2021 brainelectronics. All rights reserved.
//

#ifndef modbusRegisters_h
#define modbusRegisters_h

// ============= 8 registers in this file =============



// Outputs (COILS), SETTER+GETTER [0, 1]
#define SOME_EXAMPLE_COIL           10    //< Description of coil
#define OTHER_TESTING_COIL          11    //< [sec] Description with seconds as unit
// ============= 2 register =============



// Holding register (HREGS), SETTER+GETTER [0, 65535]
#define MY_DEFAULT_HREG             10    //< [0, 100000] Some description of this HREG with an expected range from 0 to 100.000
//                                  10    //< lower part of uint32_t
//                                  11    //< higher part of uint32_t
#define SECOND_REG_HREG             210   //< [volt] Another holding register
// ============= 2 registers =============



// Inputs (ISTS), GETTER [0, 1]
#define SSR_STATE_ISTS              10    //< state of the SSR
#define ENABLE_BUTTON_STATE_ISTS    11    //< state of the enable button
// ============= 2 registers =============



// Input register (IREGS), GETTER [0, 65535]
#define LOOP_TIME_US_IREG           10    //< [us] Time for one loop cycle
//                                  10    //< lower part of uint32_t
//                                  11    //< higher part of uint32_t
#define UPTIME_MS_IREG              12    //< [ms] System uptime
//                                  12    //< lower part of uint32_t
//                                  13    //< higher part of uint32_t
// ============= 2 registers =============

#endif
