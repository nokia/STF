
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
0032 00111101 3d .--..-. Data Length                              61
                         Data                                     

*** Start of GSM Mobile App Part Phase 2+ [250] ***
                         TCAP Layer                               
0033 01100101 65 -T-..E. Continue Message                         101
0034 00111011 3b .--..-. Message Length                           59
                         Transaction Portion                      
0035 01001000 48 .--..-. Originating TX ID                        72
0036 00000001 01 .--..-. Transaction ID Length                    1
0037 00000000 00 ----.-- Originating Transaction ID               00
0038 01001001 49 .--..-. Destination TX ID                        73
0039 00000001 01 .--..-. Transaction ID Length                    1
0040 00000000 00 ----.-- Destination Transaction ID               00
                         Optional Dialogue Portion                
                         Dialogue Portion                         
0041 01101011 6b .--..-. Dialogue Portion Tag                     107
0042 00100110 26 .--..-. Length                                   38
0043 00101000 28 .--..-. External Tag                             40
0044 00100100 24 .--..-. Length                                   36
0045 00000110 06 .--..-. Object Identifier Tag                    06
0046 00000111 07 .--..-. Length                                   07
0047 00000000 00 .--..-. CCITT Q Recommendation                   4352
0048 00010001 11 
0049 10000110 86 .--..-. Document X305                            1414
0050 00000101 05 
0051 00000001 01 .--..-. Dialogue As PDU                          257
0052 00000001 01 
0053 00000001 01 .--..-. Version1                                 01
0054 10100000 a0 .--..-. ASN1-Type Tag                            160
0055 00011001 19 .--..-. Length                                   25
0056 01100001 61 ---..-. Dialogue PDU Selection                   Dialogue Response Tag
0057 00010111 17 .--..-. Response Length                          23
                         Dialog Request Optional                  
                                                                  
0058 10100001 a1 .--..-. Application Context name Tag             161
0059 00001001 09 .--..-. AC Length                                9
0060 00000110 06 .--..-. Object Identifier                        6
0061 00000111 07 .--..-. Length                                   7
0062 00000100 04 ----.-- Context Data                             04 00 00 01 ...
0063 00000000 00 
0064 00000000 00 
0065 00000001 01 
0066 00000000 00 
0067 00000001 01 
0068 00000011 03 
0069 10100010 a2 .--..-. Result Tag                               162
0070 00000011 03 .--..-. Length                                   3
0071 00000010 02 .--..-. Integer Tag                              2
0072 00000001 01 .--..-. Length                                   1
0073 00000000 00 ----.-- Associate-result                         00000000 - accepted
0074 10100011 a3 .--..-. User Source Diagnostic Tag               163
0075 00000101 05 .--..-. Length                                   5
0076 10100001 a1 ---..-. Diagnostic Selection                     dialogue service user Tag
0077 00000011 03 .--..-. Length                                   3
0078 00000010 02 .--..-. Integer Tag                              2
0079 00000001 01 .--..-. Length                                   1
0080 00000000 00 ----.-- Diagnostic Value                         00000000 - null
                         AARE Optional                            
                                                                  
                          -                                       
                         Component Portion                        
0081 01101100 6c .--..-. Component Portion Tag                    108
0082 00001011 0b .--..-. Component Portion Length                 11
                         Optional Component Portion               
                         Return Error                             
0083 10100011 a3 -T-..E. Return Error Tag                         163
0084 00001001 09 .--..-. Return Error Length                      9
                         Invoke ID                                
0085 00000010 02 .--..-. Invoke ID Tag                            2
0086 00000001 01 .--..-. Invoke ID Length                         1
0087 00000000 00 ----.-- Invoke ID                                0
                         Error Code                               
0088 00000010 02 ---..-. Error Code Tag                           Local Error Code Tag
0089 00000001 01 .--..-. Error Code Length                        01
0090 00100010 22 -T-..E. Error Code Choice                        SystemFailure
                         Mandatory Part                           
0091 00001010 0a ---..-. Choices For SystemFailureParam           NetworkResource
0092 00000001 01 .--..-. Length                                   1
0093 00000001 01 ----.-- Network Resouce                          00000001 - hlr
