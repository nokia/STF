
*** Start of MTP ***
                         MSU                                      
0000 10000011 83 
     ----0011    ----.-. Service Indicator                        SCCP
     --00----    ----.-- Spare                                    0
     10------    ----.-- Network Indicator                        10 - National Network
0001 00110101 35 K--I.-- Destination Point Code                   309
0002 01000001 41 
     --000001    
     01------    K--I.-- Origination Point Code                   201
0003 00110010 32 
0004 00000000 00 
     ----0000    
     0000----    ----.-- Signalling Link Code                     0

*** Start of SCCP ***
                         Unitdata                                 
0005 00001001 09 .--..-. Message Type                             09
0006 00000001 01 
     ----0001    ---..-. Protocol Class                           Class 1
     0000----    ----.-- Message Handling                         0000 - no special options
                         Variable Portion                         
0007 00000011 03 .---.-. Called Party Address                     Offset 0010
0008 00001011 0b .---.-. Calling Party Address                    Offset 0019
0009 00010111 17 .---.-. Data Portion Pointer                     Offset 0032
                         Called Party Address                     
0010 00001000 08 .--..-. Called Party Address Length              8
0011 01000110 46 
     -------0    .--..-. Point Code Indicator                     Excluded
     ------1-    .--..-. Subsystem Number Indicator               Included
     --0001--    ---..-. Global Title indicator                   0001 - Global title w/ nature of address
     -1------    ----.-- Routing indicator                        1 - route on SSN
     0-------    ----.-- Reserved for National use                0 - Reserved for National use
0012 11111010 fa ----.-- Subsystem Number                         11111010 - reserved for national networks
0013 10000000 80 
     -0000000    ----.-- Nature of Address                        0000000 - unknown
     1-------    ----.-- Odd Number of Address Signals            1 - odd number
0014 10001001 89 ------- Address information                      9876543210
0015 01100111 67 
0016 01000101 45 
0017 00100011 23 
0018 00000001 01 
                         Calling Party Address                    
0019 00001100 0c .--..-. Calling Party Address Length             12
0020 01010011 53 
     -------1    .--..-. Point Code Indicator                     Included
     ------1-    .--..-. Subsystem Number Indicator               Included
     --0100--    ---..-. Global Title indicator                   0100 - Global title w/ tt, np, es, noa
     -1------    ----.-- Routing indicator                        1 - route on SSN
     0-------    ----.-- Reserved for National use                0 - Reserved for National use
0021 00110101 35 ----.-- Signalling Point Code                    309
0022 00000001 01 
0023 11111010 fa ---I.-- Subsystem Number                         11111010 - reserved for national networks
0024 00000000 00 ----.-- Translation Type                         0
0025 00000000 00 
     ----0000    ----.-- Encoding scheme                          0000 - unknown
     0000----    ----.-- Numbering plan                           0000 - unknown
0026 00000000 00 
     -0000000    ----.-- Nature of Address                        0000000 - unknown
     0-------    ----.-- Odd Number of Address Signals            0
0027 00100001 21 ------- Address information                      1234567890
0028 01000011 43 
0029 01100101 65 
0030 10000111 87 
0031 00001001 09 
0032 00011110 1e .--..-. Data Length                              30
                         Data                                     

*** Start of GSM Mobile App Part Phase 2 [5,7-10] ***
                         TCAP Layer                               
0033 01100101 65 -T-..E. Continue Message                         101
0034 00011100 1c .--..-. Message Length                           28
                         Transaction Portion                      
0035 01001000 48 .--..-. Originating TX ID                        72
0036 00000010 02 .--..-. Transaction ID Length                    2
0037 10000100 84 ----.-- Originating Transaction ID               84 de
0038 11011110 de 
0039 01001001 49 .--..-. Destination TX ID                        73
0040 00000011 03 .--..-. Transaction ID Length                    3
0041 00001001 09 ----.-- Destination Transaction ID               09 14 12
0042 00010100 14 
0043 00010010 12 
                         Optional Dialogue Portion                
                         -                                        
                         Optional Component Portion               
                         Component Portion                        
0044 01101100 6c .--..-. Component Portion Tag                    108
0045 00010001 11 .--..-. Component Portion Length                 17
                         Return Result (Last)                     
0046 10100010 a2 .--..-. Return Result (Last) Tag                 162
0047 00001111 0f .--..-. Return Result Length                     15
                         Invoke ID                                
0048 00000010 02 .--..-. Invoke ID Tag                            2
0049 00000001 01 .--..-. Invoke ID Length                         1
0050 00000000 00 ----.-- Invoke ID                                0
                         Optional MAP Operation Sequence          
0051 00110000 30 .--..-. Sequence Tag                             48
0052 00001010 0a .--..-. Length                                   10
                         MAP Operation Code                       
0053 00000010 02 ---..-. Operation Code Tag                       Local Operation Code
0054 00000001 01 .--..-. Operation Code Length                    01
0055 00111010 3a -T-..E. MAP Operation                            sendIMSI
0056 00000100 04 .--..-. IMSI                                     4
0057 00000101 05 .--..-. Length                                   5
0058 00100001 21 ------- IMSI Digits                              1234567890
0059 01000011 43 
0060 01100101 65 
0061 10000111 87 
0062 00001001 09 
                         -                                        
