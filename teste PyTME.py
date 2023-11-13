#import pdb; pdb.set_trace()
from PyTME import *



goto_xy(1,1)
text("abracadabra")
for i in range(65):
	print(i,chr(i))
	text_ln(str(i)+' '+chr(i))

goto_xy(2,2)
text("hHpAsT1LomeAsou")
delay(3000)
goto_xy(3,2)
text("12345678901234567890123456789012345678901234567890123456789012345678901234567890")

delay(3000)
clr_scr()
text_ln('ok - 1')
text_ln('ok - 2')
text_ln('ok - 3')
text_ln('ok - 4')
text('nok - 1')
text(' - nok - 2')
text(' - nok - 3')
text(' - nok - 4')

delay(3000)
goto_xy(20,24)
for i in range(20):
    text(str(i)*i)
    delay(50)

delay(1000)
goto_xy(1,15)
for i in range(20):
    text_ln(str(i))
    delay(50)

delay(1000)
clr_scr()
for i in range(25):
    goto_xy(1,i+1)
    text("12345678901234567890123456789012345678901234567890123456789012345678901234567890")

print("agora...")


print("pressione uma tecla...")
tecla=read_key()
goto_xy(15,20)
#import pdb;pdb.set_trace()
text("===>"+tecla)
delay(3000)
print("pressione uma tecla...")
read_key()
text("===>"+tecla)
for a in range(25):
    for b in range(80):
        if b==24:
            #import pdb;pdb.set_trace()
            pass
        goto_xy(b+1,a+1)
        #goto_xy(5,5)
        text("X")
        #print(a,b)
        if is_key_pressed():
            goto_xy(15,20)
            text("OOOOOO")
            print("tecla pressionada")
        else:
            goto_xy(15,20)
            text("      ")
            print("tecla nao pressionada")
            
read_key()

clr_scr()
goto_xy(35,12)
text("TERMINOU!!!")
print ("terminou")

