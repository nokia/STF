
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
0032 01001010 4a .--..-. Data Length                              74
                         Data                                     

*** Start of GSM Mobile App Part Phase 2+ [250] ***
                         TCAP Layer                               
0033 01100010 62 -T-..E. Begin Message                            98
0034 01001000 48 .--..-. Message Length                           72
                         Transaction Portion                      
0035 01001000 48 .--..-. Originating TX ID                        72
0036 00000001 01 .--..-. Transaction ID Length                    1
0037 00000000 00 ----.-- Originating Transaction ID               00
                         Optional Dialogue Portion                
                         Dialogue Portion                         
0038 01101011 6b .--..-. Dialogue Portion Tag                     107
0039 00011110 1e .--..-. Length                                   30
0040 00101000 28 .--..-. External Tag                             40
0041 00011100 1c .--..-. Length                                   28
0042 00000110 06 .--..-. Object Identifier Tag                    06
0043 00000111 07 .--..-. Length                                   07
0044 00000000 00 .--..-. CCITT Q Recommendation                   4352
0045 00010001 11 
0046 10000110 86 .--..-. Document X305                            1414
0047 00000101 05 
0048 00000001 01 .--..-. Dialogue As PDU                          257
0049 00000001 01 
0050 00000001 01 .--..-. Version1                                 01
0051 10100000 a0 .--..-. ASN1-Type Tag                            160
0052 00010001 11 .--..-. Length                                   17
0053 01100000 60 ---..-. Dialogue PDU Selection                   Dialogue Request Tag
0054 00001111 0f .--..-. Request Length                           15
                         Dialog Request Optional                  
                         Protocol Version                         
0055 10000000 80 .--..-. Protocol Version Tag                     128
0056 00000010 02 .--..-. Length                                   2
0057 00000111 07 ----.-. Unused Bits                              07
0058 00000000 00 ----.-- Protocol Version                         00
                                                                  
0059 10100001 a1 .--..-. Application Context name Tag             161
0060 00001001 09 .--..-. AC Length                                9
0061 00000110 06 .--..-. Object Identifier                        6
0062 00000111 07 .--..-. Length                                   7
0063 00000100 04 ----.-- Context Data                             04 00 00 01 ...
0064 00000000 00 
0065 00000000 00 
0066 00000001 01 
0067 00000000 00 
0068 00010001 11 
0069 00000011 03 
                         AARQ Optional                            
                                                                  
                          -                                       
                         Optional Component Portion               
                         Component Portion                        
0070 01101100 6c .--..-. Component Portion Tag                    108
0071 00100011 23 .--..-. Component Portion Length                 35
                         Invoke Component                         
0072 10100001 a1 -T-..E. Invoke Tag                               161
0073 00100001 21 .--..-. Invoke Length                            33
                         Invoke ID                                
0074 00000010 02 .--..-. Invoke ID Tag                            2
0075 00000001 01 .--..-. Invoke ID Length                         1
0076 00000000 00 ----.-- Invoke ID                                0
                         Optional Linked ID                       
                          -                                       
                         Operation Code                           
0077 00000010 02 ---..-. Operation Code Tag                       Local Operation Code
0078 00000001 01 .--..-. Operation Code Length                    01
0079 00001000 08 -T-..E. MAP Operation                            DeleteSubscriberData
0080 00110000 30 .--..-. Parameter Sequence Tag                   48
0081 00011001 19 .--..-. Parameter Length                         25
                         Mandatory Part                           
0082 10000000 80 .--..-. IMSI Tag                                 128
0083 00000110 06 .--..-. Length                                   6
0084 00100001 21 ------- IMSI Digits                              123456abcdef
0085 01000011 43 
0086 01100101 65 
0087 10111010 ba 
0088 11011100 dc 
0089 11111110 fe 
                         Optional Part                            
                         Basic Service List                       
0090 10100001 a1 .--..-. BasicServiceList Sequence Tag            161
0091 00000101 05 .--..-. Basic Service Sequence Length            5
                         Basic Service List                       
0092 10000010 82 ---..-. Basic Service Code Choice                BearerServiceCode
0093 00000011 03 .--..-. Ext Bearer Service Code Length           3
0094 00000000 00 ----.-- Ext Bearer Service Code                  00000000 - allBearerServices
0095 11000100 c4 .--..-- Future Use                               c4 48
0096 01001000 48 
                         Basic Service List - Additional Elements 
                         RoamingRestrictionDueToUnsupportedFeatur 
0097 10000100 84 .--..-. RoamingRestrictDueToUnsupportedFeat Tag  132
0098 00000000 00 .--..-. NULL Length                              00
                         vbsGroupIndication                       
0099 10000111 87 .--..-. vbsGroupIndication Tag                   135
0100 00000000 00 .--..-. NULL Length                              00
                         gprsSubscriptionDataWithDraw             
0101 10101010 aa .--..-. gprsSubscriptionDataWithDraw Tag         170
0102 00000010 02 .--..-. Length                                   2
0103 00000101 05 ---..-. gprsSubscriptionDataWithDraw Choice      allGPRSData Tag
0104 00000000 00 .--..-. NULL Length                              00
                         roamingResInSgsnDueToUnsupportedfeature  
0105 10001011 8b .--..-. roamingResInSgsnDueToUnsupFeature  Tag   139
0106 00000000 00 .--..-. NULL Length                              00
                         Vendor Specific Octets                   
                          -                                       
