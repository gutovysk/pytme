from tkinter import *
from tkinter.font import Font

class Pytme:

    window = None
    canvas = None

    titulo = "APFJogos - Python Text Mode Emulator (PyTME)"
    qtdColunas = 80
    qtdLinhas = 25
    fontSize = 13
    #fonte = Font(font=("Courier", fontSize, "normal"))
    fonte=('Courier', '13', 'normal')
    char_width = 10 ### trocar esse valor constante de acordo com o tipo da fonte
    char_height = 16 ### trocar esse valor constante de acordo com o tipo da fonte
    width = None
    height = None
    back_ground_color = "BLACK"
    text_color = "WHITE"
    opcoes_do_texto = {"font":fonte, "anchor":NW, "fill":text_color,
                       "offset":"0,0", "justify":"left", "activefill":"red"}
    opcoes_da_janela = {"width":qtdColunas * char_width,"height":qtdLinhas * char_height, "bd":0, "bg":back_ground_color}

    texto = ' ' * qtdColunas
    conteudo = [texto] * qtdLinhas
    cursor_X = 1
    cursor_Y = 1
    cursor_On = True  # indica se cursor aparece ou não na tela
    cursor_insert = True  # indica se cursor está no modo de 'insert'
    cursor_typing_text = False  # indica se cursor está no modo de edição
    cursor_XORMode = True  # indica se cursor deve imprimir no modo XORMode ou PaintMode
    cursor_ticks = 500  # tempo em ms para o cursor piscar (blink)
    is_key_pressed = False
    #char keyPressed = Character.UNASSIGNED
    code_key_pressed = -1



    #**  método de inicialização da janela  **#

    def __init__(self):
        print("entrei aqui")
        self.window = Tk()
        self.window.resizable(width=False, height=False)
        self.window.title(self.titulo)
        self.canvas = Canvas(self.window, **self.opcoes_da_janela)
        self.canvas.pack()

    def init(self):
        if not canvas:
            print('kkk')
        """
        f = new JFrame()
        f.setTitle("APFJogos - Java Text Mode Emulator (JTME)")

        f.setContentPane(new Jtme())
        resetColors()
        f.setFont(fonte)
        f.getContentPane().setBackground(backgroundColor)
        f.getContentPane().setFont(fonte)
        KeyboardFocusManager manager = KeyboardFocusManager.getCurrentKeyboardFocusManager()
        manager.addKeyEventDispatcher((KeyEventDispatcher) f.getContentPane())

        FontMetrics fonteM = f.getFontMetrics(f.getFont())
        int ascent = fonteM.getMaxAscent()
        int descent = fonteM.getMaxDescent()
        int advance = fonteM.getMaxAdvance() // ou talvez fonteM.getWidths()[65]
        charWidth = advance
        charHeight = descent + ascent

        charWidth = 8      // o correto seria achar os valores de acordo com font e size
        charHeight = 12

        height = charHeight * qtdLinhas
        width = charWidth * (qtdColunas-1)

        f.getContentPane().setPreferredSize(new Dimension(width,height))
        f.pack()  // acrescenta 40 pixels na altura e 16 pixels das bordas

        f.setLocationRelativeTo(null)
        f.setResizable(false)
        f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE)
        f.setVisible(true)

        clrScr()

        print("ascent=" + ascent + ", descent= " + descent
              + ", advance=" + advance + ". width=" + width + ", height="+ height)
    """

    def update_graphics(self):
        linha = 0
        for texto in self.conteudo:
            self.canvas.create_text(2,linha * self.char_height, text=texto,
                                **self.opcoes_do_texto)
            linha+=1


    def goto_xy(self, x=0, y=0):
        self.cursor_X=x
        self.cursor_Y=y

    def text(self,texto=None):
        #self.canvas.create_text(0,80, text="aaaaffdyyyfft_yftyftybytx mbm hyyyuuuihu",
        #      fill="white", offset="0,0", justify="left", activefill="red",
        #      anchor=NW, font=('Courier', '13', 'normal'))
        #self.canvas.create_text(0,0, text=texto,
        #                        **self.opcoes_do_texto)
        if texto:
            x=self.cursor_X-1
            y=self.cursor_Y-1
            l=len(texto)
            s=self.conteudo[x]
            self.conteudo[x]=s[:y] + texto + s[y+l:]
            self.cursor_Y=self.cursor_Y+l
            #print (self.conteudo)
        self.update_graphics()


x=Pytme()
x.goto_xy(2,1)
x.text("hHpçT1Lomeçou")
x.goto_xy(3,1)
x.text("12345678901234567890123456789012345678901234567890123456789012345678901234567890")

for i in range(25):
    x.goto_xy(i+1,1)
    x.text("12345678901234567890123456789012345678901234567890123456789012345678901234567890")
    
for a in range(25):
    for b in range(80):
        x.goto_xy(a+1,b)
        x.text("X")
 
print ("começou")

