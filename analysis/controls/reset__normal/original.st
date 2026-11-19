PROGRAM p
VAR
start AT %IX0.0:BOOL;
hazard AT %IX0.1:BOOL;
reset AT %IX0.2:BOOL;
pump:BOOL; armed:BOOL; c:INT;
END_VAR
IF reset THEN
 c := 0;
ELSE
 c := c + 1;
END_IF;
IF c >= 1023 THEN
 armed := TRUE;
END_IF;
IF start AND NOT hazard THEN
 pump := TRUE;
END_IF;
IF hazard THEN
 pump := FALSE;
END_IF;
END_PROGRAM
