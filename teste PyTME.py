#import pdb; pdb.set_trace()
from PyTME import *


x=Pytme()
x.goto_xy(1,1)
x.text("abracadabra")
for i in range(65):
	print(i,chr(i))
	x.text_ln(str(i)+' '+chr(i))

x.goto_xy(2,2)
x.text("hHpAsT1LomeAsou")
x.delay(3000)
x.goto_xy(3,2)
x.text("12345678901234567890123456789012345678901234567890123456789012345678901234567890")

x.delay(3000)
x.clr_scr()
x.text_ln('ok - 1')
x.text_ln('ok - 2')
x.text_ln('ok - 3')
x.text_ln('ok - 4')
x.text('nok - 1')
x.text(' - nok - 2')
x.text(' - nok - 3')
x.text(' - nok - 4')

x.delay(3000)
x.goto_xy(20,24)
for i in range(20):
    x.text(str(i)*i)
    x.delay(50)

x.delay(1000)
x.goto_xy(1,15)
for i in range(20):
    x.text_ln(str(i))
    x.delay(50)

x.delay(1000)
x.clr_scr()
for i in range(25):
    x.goto_xy(1,i+1)
    x.text("12345678901234567890123456789012345678901234567890123456789012345678901234567890")

print("agora...")


print("pressione uma tecla...")
tecla=x.read_key()
x.goto_xy(15,20)
#import pdb;pdb.set_trace()
x.text("===>"+tecla)
x.delay(3000)
print("pressione uma tecla...")
x.read_key()
x.text("===>"+tecla)
for a in range(25):
    for b in range(80):
        if b==24:
            #import pdb;pdb.set_trace()
            pass
        x.goto_xy(b+1,a+1)
        #x.goto_xy(5,5)
        x.text("X")
        #print(a,b)
        if x.is_key_pressed():
            x.goto_xy(15,20)
            x.text("OOOOOO")
            print("tecla pressionada")
        else:
            x.goto_xy(15,20)
            x.text("      ")
            print("tecla nao pressionada")
            
x.read_key()

x.clr_scr()
x.goto_xy(35,12)
x.text("TERMINOU!!!")
print ("terminou")

