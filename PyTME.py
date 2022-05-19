"""
    * APFJogos - Python Text Mode Emulator (PyTME)
    *   versao:1.0
    *   data da ultima revisao: 12/08/2016
    *   por: Carlos A. Correia
    * 
    * A classe <code>Pytme</code> emula o Modo Texto com diversas funcionalidades.
    * Ela pode ser instanciada, estendida, ou simplesmente indicar o uso da classe
    * como estatica. Veja exemplo de como imprimir um texto:
    * 
    * Pytme.print("texto")
    * 
    * ou se sua classe estender (extends) Pytme, entao bastaria usar a instrucao diretamente:
    * 
    * print("texto");
    * 
    * 
    * <p> As principais funcoes sao:
    *   clrScr(); clrEol();
    * 	print(String); println(String);
    * 	isKeyPressed(); readKey(); typeText();
    * 
    * Esta classe foi concebida para ser usada na Colecao Aprenda a Programar Fazendo Jogos
    * 
    * Modifique-a ao seu gosto, e cite a fonte de uso.
    *
    * @author  Carlos Correia
    * 
"""


#import tkinter as tk
try:
    import Tkinter as tk
    import tkFont as font
except:
    import Tkinter as tk
    from tkinter.font import Font as font



class Pytme:

    window = None
    canvas = None

    titulo = "APFJogos - Python Text Mode Emulator (PyTME)"
    qtd_colunas = 80
    qtd_linhas = 25
    font_size = 13
    #fonte = Font(font=("Courier", font_size, "normal"))
    fonte=('Courier', '13', 'normal')
    char_width = 10 ### trocar esse valor constante de acordo com o tipo da fonte
    char_height = 16 ### trocar esse valor constante de acordo com o tipo da fonte
    width = None
    height = None
    BACK_GROUND_COLOR_DEFAULT = "BLACK"
    TEXT_COLOR_DEFAULT = "WHITE"
    opcoes_do_texto = {"font":fonte, "anchor":tk.NW, "fill":TEXT_COLOR_DEFAULT}
    opcoes_da_janela = {"width":qtd_colunas * char_width+2,
                        "height":qtd_linhas * char_height+2,
                        "bd":0, "bg":BACK_GROUND_COLOR_DEFAULT,
                        "takefocus":1, "highlightthickness":0}

    conteudo = ' ' * qtd_colunas * qtd_linhas
    qtd_chars = len (conteudo)
    #caracteres_ = {chr(i): "" for i in range(32)} #caracteres especiais
    cursor_X = 1
    cursor_Y = 1
    cursor_on = True            # indica se cursor aparece ou nao na tela
    cursor_insert = True        # indica se cursor esta no modo de 'insert'
    cursor_typing_text = False  # indica se cursor esta no modo de edicao
    cursor_XOR_mode = True      # indica se cursor deve imprimir no modo XORMode ou PaintMode
    cursor_ticks = 500          # tempo em ms para o cursor piscar (blink)
    #is_key_pressed = False
    key_pressed = None
    code_key_pressed = None


    ###  metodo de inicializacao da janela  ###

    def __init__(self):
        print("entrei aqui")
        self.window = tk.Tk()
        self.window.resizable(width=False, height=False)
        self.window.title(self.titulo)
        self.canvas = tk.Canvas(self.window, **self.opcoes_da_janela)
        self.canvas.focus_set()
        self.canvas.bind("<Key>", self.key_pressed)
        self.canvas.bind("<KeyRelease>", self.on_key_released)
        self.canvas.pack()
        self.set_key_released()

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

        height = charHeight * qtd_linhas
        width = charWidth * (qtd_colunas-1)

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

    ###  metodos referentes a janela Canvas: paint() ###

    def paint(self): #Graphics g):
        self.canvas.delete("all")
        linha = 0
        for linha in range(self.qtd_linhas):
            z=linha*self.qtd_colunas
            self.canvas.create_text(2,linha * self.char_height,
                                    text=self.conteudo[z:z+self.qtd_colunas],
                                    **self.opcoes_do_texto)
        self.canvas.update()

        if (self.cursor_on):
        	if (self.cursor_XOR_mode):
        		print("kkk")
        #        g.setXORMode(Color.BLACK)
        #        if (self.cursor_insert)
        #            g.fillRect(cursorX * charWidth - charWidth, cursorY * charHeight, charWidth, 3)
        #        else
        #            g.fillRect(cursorX * charWidth - charWidth, cursorY * charHeight-charHeight+3, charWidth, charHeight)





    """
    @Override
    def actionPerformed(ActionEvent arg0) {
        if (cursor_typing_text) {
            cursor_XOR_mode = !cursor_XOR_mode;
            self.paint()
        }

    @Override
    def dispatchKeyEvent(KeyEvent e) {
        if (e.getID() == KeyEvent.KEY_PRESSED) {
            keyPressed(e);
        } elif (e.getID() == KeyEvent.KEY_RELEASED) {
            keyReleased(e);
          } elif (e.getID() == KeyEvent.KEY_TYPED) {
              keyTyped(e);
        }
        return false;
    }

    def keyPressed(KeyEvent e) {
        keyPressed = e.getKeyChar();
        codeKeyPressed = e.getKeyCode();
        isKeyPressed = true;
    }

    def keyTyped(KeyEvent e) {
        isKeyPressed = true;
    }

    def keyReleased(KeyEvent e) {
        setKeyReleased();
    }


    """

    ###  metodos referente ao cursor de impressao  ###


    def goto_xy(self, x=0, y=0):

        #if (f==null) init();
        if (x < 1) or (x > self.qtd_colunas):
            x = 1
            y = 1

        if (y < 1) or (y > self.qtd_linhas):
            x = 1
            y = 1

        self.cursor_X = x
        self.cursor_Y = y
        #self.paint()

    def set_cursor_on(self):
        #if (f==null) init();
        self.cursor_on = True;
        #self.paint()

    def set_cursor_off(self):
        #if (f==null) init()
        self.cursor_on = False
        #f.repaint()

    def set_cursor_mode(self, b = True):
        #if (f==null) init()
        self.cursor_on = b
        #self.paint()

    def get_cursor_mode(self):
        return self.cursor_on

    def get_cursor_X(self):
        return self.cursor_X

    def get_cursor_Y(self):
        return self.cursor_Y

    def change_cursor_state(self):
        print("piscou")
    	if (self.cursor_typing_text):
            self.cursor_XOR_mode = not self.cursor_XOR_mode
            #self.paint()


    ###  metodos de insercao de conteudo  ###

    def insert_text_xy_in_content(self, x=1, y=1, texto=''):
        #import pdb;pdb.set_trace()
        x-=1
        y-=1
        pos_i=y*self.qtd_colunas+x
        tam=len(texto)
        pos_f=pos_i+tam
        texto=texto.replace(chr(13),'')
        self.conteudo=self.conteudo[:pos_i] + texto + self.conteudo[pos_f:]
        y=pos_f // self.qtd_colunas+1
        x=pos_f % self.qtd_colunas+1
        return x,y

    def zero_content(self):
        self.conteudo = ' ' * self.qtd_colunas * self.qtd_linhas

    def insert_xy_to_eol(self, x=1, y=1, char=' ', qtd=0):
        texto = char*(self.qtd_colunas-x+1)
        self.insert_text_xy_in_content(x,y,texto)

    def carriage_return_line_feed(self):
        self.cursor_X = 1
        self.cursor_Y +=1
        if self.cursor_Y > self.qtd_linhas:
            #import pdb;pdb.set_trace()
            self.insert_xy_to_eol(x=1, y=self.cursor_Y, qtd=self.qtd_linhas)
            self.cursor_Y = self.qtd_linhas


    ###  metodos referente a tela: clrScr (apagar a tela toda)   ###

    def clr_scr(self):
        #if (f==null) init()

        self.zero_content()
    
        self.goto_xy(1, 1)
        self.paint() ###  <= se goto_xy chamar paint() entao essa linha nao sera necessaria

    def clr_eol(self):
        #if (f==null) init()
        x = self.get_cursor_X()
        y = self.get_cursor_Y()
        self.insert_xy_to_eol(x=x, y=y)

        self.goto_xy(x, y)
        self.paint() ###  <= se goto_xy chamar paint() entao essa linha nao sera necessaria


    ###  metodos de mudanca de cores da tela   ###

    def reset_colors(self):
        back_ground_color = BACK_GROUND_COLOR_DEFAULT
        text_color = TEXT_COLOR_DEFAULT
        opcoes_do_texto["fill"]=text_color


    def set_back_ground_color(self, back_ground_color = BACK_GROUND_COLOR_DEFAULT):
        pass
        #opcoes_do_texto["fill"]=text_color

    def set_text_color(self, text_color = TEXT_COLOR_DEFAULT):
        opcoes_do_texto["fill"]=text_color


    ###  metodos de impressao na tela   ###

    def printing_text(self, texto=None):
        #if (f==null) init()

        if texto:
            #import pdb;pdb.set_trace()
            texto=str(texto)
            texto=texto.replace(chr(13),'')
            x=self.get_cursor_X()
            y=self.get_cursor_Y()
            self.cursor_X,self.cursor_Y=self.insert_text_xy_in_content(x,y,texto)

            if (self.cursor_Y > self.qtd_linhas):
                #import pdb;pdb.set_trace()
                self.clr_eol()
                self.cursor_Y = self.qtd_linhas
                #self.carriage_return_line_feed()

            self.conteudo=self.conteudo[-self.qtd_chars:]

            self.paint()

    def text(self, *args):
    	for texto in args:
    		self.printing_text(texto)

    def text_ln(self, *args):
        self.printing_text(*args)
        self.carriage_return_line_feed()


    ###  metodo de temporizacao  ###

    def delay(self, milliseconds=0):
        self.canvas.after(milliseconds)


    ### metodos referente a leitura de teclados: bind()

    def set_key_released(self):
        #self.is_key_pressed = False
        self.key_pressed = None
        self.code_key_pressed = None

    def get_key_pressed(self):
    	return self.key_pressed

    def get_key_code_pressed(self):
    	return self.code_key_pressed

    def key_pressed(self, event):
        self.key_pressed = event.char
        self.code_key_pressed = event.keycode
        #self.is_key_pressed = True
        print ("tecla_pressionada = "+self.key_pressed,self.code_key_pressed,self.is_key_pressed()," - ",event.char)

    def on_key_released(self, event):
        self.set_key_released()
        print ("tecla_solta")

    def is_key_pressed(self):
        #if (f==null) init()
        #delay(0)
        return (self.key_pressed != None)

    def read_key(self):
        while self.is_key_pressed(): ### *necessario para pegar apenas uma tecla por vez!
            self.canvas.update()
            
        while (not self.is_key_pressed()):
            self.canvas.update()
            #self.delay(1)  ### *necessario para funcionar em computadores mais rapidos!
        return self.key_pressed


    def typing_text(self):
    	def insert_str(string, str_to_insert, index, insert=True):
    		return string[:index] + str_to_insert + string[(index if insert else index+len(str_to_insert)):]

    	def delete_char_at(string, index):
    		return string[:index]+string[(index+1):]

        s = "" #new StringBuffer("");
        x_cursor_inicial = self.get_cursor_X()
        y_cursor_inicial = self.get_cursor_Y()
        index_string = 0
        x_cursor = x_cursor_inicial
        y_cursor = y_cursor_inicial
        cursor_mode = self.get_cursor_mode()   ## para voltar ao estado inicial do cursor
        self.cursor_XOR_mode = True                 ## para comecar com o cursor impresso na tela
        self.set_cursor_on()                   ## e forcar edicao de texto com cursor piscando na tela
        self.cursor_typing_text=True                ## indica que o cursor pisca no modo de edicao

		
        self.canvas.after(self.cursor_ticks, self.change_cursor_state())
        #self.canvas.mainloop()
        #timer.start();
		


        while True:
            self.set_key_released()          ## para zerar o buffer da tecla impedindo de acrescentar varios caracteres
            c = self.read_key();
            ord_tecla=self.code_key_pressed
            if (len(s) < 256 and len(c)>0):           ## texto maximo de 256 caracteres
                if (c >= " " and c <= chr(126)):
                    if (self.cursor_insert or (index_string==len(s))):  ## acrescentar um caractere
                        s=insert_str(s,c,index_string)
                        print(s,c,index_string,len(s))
                    else:
                    	s=insert_str(s,c,index_string,False)              ## substituir um caractere (<insert>=off)
                    index_string+=1
            if ord_tecla==37:    ## <VK_LEFT>
                index_string-=1
            if ord_tecla==39:                     ## <VK_RIGHT>
            	index_string+=1
            if ord_tecla==8:                      ## <VK_BACKSPACE>
                if (index_string>0):
                    s=delete_char_at(s,index_string - 1)
                    index_string-=1
            if ord_tecla==46:                    ## <VK_DEL>
                if (index_string < len(s)):
                    s=delete_char_at(s,index_string)
            if ord_tecla==36:                     ## <VK_HOME>
                index_string = 0
            if ord_tecla==35:                     ## <VK_END>
                index_string = len(s)
            if ord_tecla==155:                    ## <VK_INSERT>
                self.cursor_insert = not self.cursor_insert
            if (index_string < 0):
                index_string = 0
            if (index_string > len(s)):
                index_string = len(s)
            self.goto_xy(x_cursor_inicial, y_cursor_inicial)
            self.text(s)
            if (ord_tecla == 8) or (ord_tecla == 46):   ## imprimir um caracter em branco no final da
                self.text(" ")                         ## string, caso algum caractere tenha sido deletado
                x_cursor = 1 + (index_string + x_cursor_inicial - 1) % (self.qtd_colunas)  ## calcula posicao do cursor em funcao de index_string
                y_cursor = y_cursor_inicial + (index_string + x_cursor_inicial - 1) / (self.qtd_linhas)
                if (y_cursor > self.qtd_linhas):        ## quando o cursor ultrapassar a ultima linha
                    y_cursor_inicial-=1
                    y_cursor-=1

            ##cursorEditing=false  ## para permanecer o cursor ativo quando move-lo ou se inserir um caractere
            ##cursor_XOR_mode=True   ## para permanecer o cursor ativo quando move-lo ou se inserir um caractere
            
#            timer.restart()
            
            self.goto_xy(x_cursor, y_cursor)
            if (ord_tecla == 13):
            	break
#        timer.stop()
        self.set_cursor_mode(cursor_mode)  ## volta ao estado inicial do cursor
        self.cursor_typing_text = False   ## indica que nao esta no modo de digitacao
        self.cursor_XOR_mode = True       ## indica que o cursor nao pisca fora do modo de edicao
        self.cursor_insert = True        ## sai do modo de edicao forcando <insert>=On
        return s

    def type_textln(self, *args):
    	self.text_ln(*args)
        texto = self.type_text()
        self.carriage_return_line_feed()
        return texto

    def type_text(self, *args):
        self.text(*args)
        return self.typing_text()

    def typeTextln(self, *args):
        print(args)
        texto = self.type_text()
        self.carriage_return_line_feed()
        return texto


"""
 *	Falta fazer:
 *  
 *  1- melhorar a velocidade do piscar do cursor para que fique igual, ou parecido, na maioria das CPUs
 *  2- verificar tamanho da fonte para colocar espacamento correto
 *  3- retirar syso do init() quando terminar o item 2 acima
 *  4- melhorar a constancia de velocidade nas interacoes (ora fica mais lento, ora fica no tempo normal)
 * 
"""

