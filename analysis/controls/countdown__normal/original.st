PROGRAM p
VAR
start AT %IX0.0:BOOL;
hazard AT %IX0.1:BOOL;
pump:BOOL; armed:BOOL; c:INT:=2000;
END_VAR
c := c - 2;
IF c <= 0 THEN
 armed := TRUE;
END_IF;
IF start AND NOT hazard THEN
 pump := TRUE;
END_IF;
IF hazard THEN
 pump := FALSE;
END_IF;
END_PROGRAM
