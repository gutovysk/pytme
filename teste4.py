from PyTME import *

set_cursor_on()
text("iiijj")
delay(1400)
x=99
text("oko","kkk",7,x)
delay(400)
#import pdb;pdb.set_trace()
y=type_text("kokko"," 000:")

set_cursor_off()
goto_xy(10,10)
text(y)
delay(1000)

z=type_textln("ok:"," ")
goto_xy(10,10)
text(z)
delay(4000)