PROGRAM p
VAR
start AT %IX0.0:BOOL;
hazard AT %IX0.1:BOOL;
pump:BOOL; armed:BOOL; c:INT:=71;
END_VAR
c := c + 1;
IF c >= 2047 THEN
 armed := TRUE;
END_IF;
IF start AND NOT hazard THEN
 pump := TRUE;
END_IF;
IF hazard THEN
 pump := FALSE;
END_IF;
END_PROGRAM
