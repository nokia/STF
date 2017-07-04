
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
0032 00101011 2b .--..-. Data Length                              43
                         Data                                     

*** Start of GSM Mobile App Part Phase 2+ [250] ***
                         TCAP Layer                               
0033 01100101 65 -T-..E. Continue Message                         101
0034 00101001 29 .--..-. Message Length                           41
                         Transaction Portion                      
0035 01001000 48 .--..-. Originating TX ID                        72
0036 00000001 01 .--..-. Transaction ID Length                    1
0037 00000000 00 ----.-- Originating Transaction ID               00
0038 01001001 49 .--..-. Destination TX ID                        73
0039 00000001 01 .--..-. Transaction ID Length                    1
0040 00000000 00 ----.-- Destination Transaction ID               00
                         Optional Dialogue Portion                
                          -                                       
                         Component Portion                        
0041 01101100 6c .--..-. Component Portion Tag                    108
0042 00100001 21 .--..-. Component Portion Length                 33
                         Optional Component Portion               
                         Invoke Component                         
0043 10100001 a1 ....... Invoke  Tag                              161
0044 00011111 1f .--..-. Invoke Length                            31
                         Invoke ID                                
0045 00000010 02 .--..-. Invoke ID Tag                            2
0046 00000001 01 .--..-. Invoke ID Length                         1
0047 00000000 00 ----.-- Invoke ID                                0
                         Optional Linked ID                       
                          -                                       
                         Operation Code                           
0048 00000010 02 ---..-. Operation Code Tag                       Local Operation Code
0049 00000001 01 .--..-. Operation Code Length                    01
0050 00011000 18 -T-..E. MAP Operation                            SendRoutingInfoForGPRS
0051 00110000 30 .--..-. Sequence Parameter Tag                   48
0052 00010111 17 .--..-. Length                                   23
                         Mandatory Part                           
0053 10000000 80 .--..-. IMSI Tag                                 128
0054 00001000 08 .--..-. Length                                   8
0055 00100001 21 ------- IMSI Digits                              1234567890123456
0056 01000011 43 
0057 01100101 65 
0058 10000111 87 
0059 00001001 09 
0060 00100001 21 
0061 01000011 43 
0062 01100101 65 
                         Optional Part                            
                         ggsn-address                             
0063 10000001 81 .--..-. ggsn-Address Tag                         129
0064 00000101 05 .--..-. Length                                   5
0065 01011101 5d ----.-- GGSN-Address                             5d ae 95 ca ...
0066 10101110 ae 
0067 10010101 95 
0068 11001010 ca 
0069 11110011 f3 
0070 10000010 82 ----.-- Vendor Specific Octets                   82 04 c9 21 ...
0071 00000100 04 
0072 11001001 c9 
0073 00100001 21 
0074 01000011 43 
0075 00000101 05 
