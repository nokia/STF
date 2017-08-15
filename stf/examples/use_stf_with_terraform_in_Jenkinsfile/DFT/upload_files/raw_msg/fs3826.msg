
*** Start of MTP ***
                         MSU                                      
0000 10000011 83 
     ----0011    ----.-. Service Indicator                        SCCP
     --00----    ----.-- Spare                                    0
     10------    ----.-- Network Indicator                        10 - National Network
0001 00000000 00 K--I.-- Destination Point Code                   0
0002 00000000 00 
     --000000    
     00------    K--I.-- Origination Point Code                   0
0003 00000000 00 
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
0008 00000101 05 .---.-. Calling Party Address                    Offset 0013
0009 00001001 09 .---.-. Data Portion Pointer                     Offset 0018
                         Called Party Address                     
0010 00000010 02 .--..-. Called Party Address Length              2
0011 01000010 42 
     -------0    .--..-. Point Code Indicator                     Excluded
     ------1-    .--..-. Subsystem Number Indicator               Included
     --0000--    ---..-. Global Title indicator                   0000 - No global title included
     -1------    ----.-- Routing indicator                        1 - route on SSN
     0-------    ----.-- Reserved for National use                0 - Reserved for National use
0012 11111010 fa ----.-- Subsystem Number                         11111010 - reserved for national networks
                         Calling Party Address                    
0013 00000100 04 .--..-. Calling Party Address Length             4
0014 01000011 43 
     -------1    .--..-. Point Code Indicator                     Included
     ------1-    .--..-. Subsystem Number Indicator               Included
     --0000--    ---..-. Global Title indicator                   0000 - No global title included
     -1------    ----.-- Routing indicator                        1 - route on SSN
     0-------    ----.-- Reserved for National use                0 - Reserved for National use
0015 00110101 35 ----.-- Signalling Point Code                    309
0016 00000001 01 
0017 11111010 fa ---I.-- Subsystem Number                         11111010 - reserved for national networks
0018 00111011 38 .--..-. Data Length                              59
                         Data                                     

*** Start of GSM Mobile App Part Phase 2 [5,7-10] ***
                         TCAP Layer                               
0019 01100010 61 -T-..E. Unidirectional Message                            98
0020 00111001 36 .--..-. Message Length                           57
                         Transaction Portion                      
                         Optional Dialogue Portion                
                         Dialogue Portion                         
0024 01101011 6b .--..-. Dialogue Portion Tag                     107
0025 00011010 1a .--..-. Length                                   26
0026 00101000 28 .--..-. External Tag                             40
0027 00011000 18 .--..-. Length                                   24
0028 00000110 06 .--..-. Object Identifier Tag                    06
0029 00000111 07 .--..-. Length                                   7
                         Dialogue-as-ID value                     
0030 00000000 00 .--..-. CCITT Q Recommendation                   00
0031 00010001 11 .--..-. Q                                        17
0032 10000110 86 .--..-. Document 773 (X'305)                     1414
0033 00000101 05 
0034 00000001 01 .--..-. as(1)                                    01
0035 00000001 02 .--..-. dialoguePDU                              01
0036 00000001 01 .--..-. Version1 (1)                             01
0037 10100000 a0 .--..-. ASN.1-type Tag                           160
0038 00001101 0d .--..-. ASN.1-type Length                        13
0039 01100000 60 ---..-. Dialogue PDU Selection                   Dialogue Request Tag
0040 00001011 0b .--..-. Request Length                           11
                         Dialog Request Optional                  
                         -                                        
0041 10100001 a1 .--..-. Application Context name Tag             161
0042 00001001 09 .--..-. AC Length                                9
0043 00000110 06 .--..-. Object Identifier                        6
0044 00000111 07 .--..-. Length                                   7
0045 00000100 04 ----.-- Context Data                             04 00 00 01 ...
0046 00000000 00 
0047 00000000 00 
0048 00000001 01 
0049 00000000 00 
0050 00010001 11 
0051 00000001 01 
                         AARQ Optional                            
                         -                                        
                         -                                        
                         Optional Component Portion               
                         Component Portion                        
0052 01101100 6c .--..-. Component Portion Tag                    108
0053 00011000 18 .--..-. Component Portion Length                 24
                         Optional Component                       
                         Invoke Component                         
0054 10100001 a1 -T-..E. Invoke Tag                               161
0055 00010110 16 .--..-. Invoke Length                            22
                         Invoke ID                                
0056 00000010 02 .--..-. Invoke ID Tag                            2
0057 00000001 01 .--..-. Invoke ID Length                         1
0058 00000000 00 ----.-- Invoke ID                                0
                         Optional Linked ID                       
                         -                                        
                         Operation Code                           
0059 00000010 02 ---..-. Operation Code Tag                       Local Operation Code
0060 00000001 01 .--..-. Operation Code Length                    01
0061 00110011 33 -T-..E. MAP Operation                            DeactivateTraceMode
0062 00110000 30 .--..-. Sequence Tag                             48
0063 00001110 0e .--..-. Length                                   14
                         Optional IMSI                            
                         IMSI                                     
0064 10000000 80 .--..-. IMSI Tag                                 128
0065 00001000 08 .--..-. Length                                   8
0066 00100001 21 ------- IMSI Digits                              1234567890123456
0067 01000011 43 
0068 01100101 65 
0069 10000111 87 
0070 00001001 09 
0071 00100001 21 
0072 01000011 43 
0073 01100101 65 
                         -                                        
                         Mandatory Part                           
0074 10000001 81 .--..-. TraceReference                           129
0075 00000010 02 .--..-. Length                                   2
0076 00010100 14 ----.-- TraceReference Value                     14 06
0077 00000110 06 
                         Vendor Specific Octets                   
                         -                                        
