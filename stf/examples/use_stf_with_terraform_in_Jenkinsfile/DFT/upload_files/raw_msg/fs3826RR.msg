
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
                         Data                                     

*** Start of GSM Mobile Appl Part Phase 1 [254] ***
                         TCAP Layer                               
0019 00010101 12 ....... TCAP Length                              21
0020 01100100 64 .T...E. End Message                              100
0021 00010011 10 ....... Message Length                           19
                         Transaction Portion                      
0022 01001001 49 ....... Destination TX ID                        73
0023 00000010 02 ....... Transaction ID Length                    2
0024 01000000 40 .---.-- Destination Transaction ID               40 88
0025 10001000 88 
                         Component Portion                        
0026 01101100 6c ....... Component Portion Tag                    108
0027 00001101 0a ....... Component Portion Length                 13
                         Return Result (Last)                     
0028 10100010 a2 .T...E. Return Result (Last) Tag                 162
0029 00001011 08 ....... Return Result Length                     11
                         Invoke ID                                
0030 00000010 02 ....... Invoke ID Tag                            2
0031 00000001 01 ....... Invoke ID Length                         1
0032 11111100 fc .---.-- Invoke ID                                252
                         Optional Linked ID                       
                                                                  
0036 00110000 30 ....... Sequence Tag                             48
0037 00000011 03 ....... Length                                   3
                         Operation Code                           
0038 00000010 02 ....... Operation Code Tag                       Local Operation Code
0039 00000001 01 ....... Operation Code Length                    01
0040 00110011 33 .-...-. MAP Operation                            DeactivateTraceMode
