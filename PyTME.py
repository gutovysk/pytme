"""
    * APFJogos - Python Text Mode Emulator (PyTME)
    *   versao: 1.3 (correcao do is_key_pressed em modo polling)
    *   data da revisao original: 12/11/2023
    *   data desta revisao: 18/05/2026
    *   por: Carlos A. Correia (revisao com correcoes)
    *
    * A classe Pytme emula o Modo Texto com diversas funcionalidades.
    * Veja exemplo de como imprimir um texto:
    *
    *   Pytme.print("texto")
    *
    * ou, se sua classe estender Pytme, basta usar a instrucao diretamente:
    *
    *   print("texto")
    *
    * As principais funcoes sao:
    *   clr_scr(); clr_eol();
    *   text(String); textln(String);
    *   is_key_pressed(); read_key(); type_text(); type_textln();
    *
    * Esta classe foi concebida para ser usada na Colecao
    * "Aprenda a Programar Fazendo Jogos".
    *
    * Modifique-a ao seu gosto, e cite a fonte de uso.
    *
    * @author  Carlos Correia
    *
    *
    * --- CORRECOES nesta versao ---
    *  1. reset_colors/set_text_color/set_back_ground_color agora funcionam
    *     (usavam nomes nao qualificados).
    *  2. set_back_ground_color realmente muda a cor de fundo do Canvas.
    *  3. Buffer "conteudo" agora e truncado corretamente quando escritas
    *     ultrapassam a tela (antes descartava o inicio em vez do fim).
    *  4. delay() agora realmente espera (e processa eventos no meio tempo).
    *  5. read_key() nao faz mais busy-loop a 100% de CPU.
    *  6. carriage_return_line_feed agora faz scroll real (estilo terminal).
    *  7. typing_text/type_text com cursor que pisca de verdade.
    *  8. Tamanho da fonte e medido dinamicamente.
    *  9. \n agora e tratado como quebra de linha.
    * 10. Tela e desenhada (limpa) no __init__.
"""


try:
    import Tkinter as tk
    import tkFont
    _Font = tkFont.Font
except ImportError:
    import tkinter as tk
    from tkinter.font import Font as _Font

import time


class Pytme:

    window = None
    canvas = None

    titulo = "APFJogos - Python Text Mode Emulator (PyTME)"
    qtd_colunas = 80
    qtd_linhas = 25
    font_size = 13
    fonte = ('Courier', '13', 'normal')
    # Estes valores sao apenas defaults; serao recalculados no __init__
    # de acordo com a fonte real.
    char_width = 10
    char_height = 16
    width = None
    height = None
    BACK_GROUND_COLOR_DEFAULT = "BLACK"
    TEXT_COLOR_DEFAULT = "WHITE"

    conteudo = ' ' * qtd_colunas * qtd_linhas
    qtd_chars = len(conteudo)

    cursor_X = 1
    cursor_Y = 1
    cursor_color = "WHITE"
    cursor_on = True             # indica se o cursor pode aparecer na tela
    cursor_blink_visible = True  # estado atual do blink (True=visivel)
    cursor_insert = True         # modo INSERT (True) ou OVERWRITE (False)
    cursor_typing_text = False   # indica se cursor esta no modo de edicao
    cursor_XOR_mode = True       # mantido por compat. com a API original
    cursor_ticks = 500           # tempo em ms para o cursor piscar
    cursor_blinking_after = None # id do timer atual de piscar

    key_pressed = None
    code_key_pressed = None

    # Usado pelo loop event-driven de typing_text:
    _typing_key_var = None

    ###  metodo de inicializacao da janela  ###

    def __init__(self):
        self.window = tk.Tk()
        self.window.resizable(width=False, height=False)
        self.window.title(self.titulo)

        # Medir a fonte de verdade em vez de chutar 10x16.
        try:
            f = _Font(family=self.fonte[0], size=int(self.fonte[1]))
            measured_w = f.measure('M')
            measured_h = f.metrics('linespace')
            if measured_w > 0:
                self.char_width = measured_w
            if measured_h > 0:
                self.char_height = measured_h
            self.cursor_width = self.char_width
            self.cursor_height = max(2, self.char_height // 4)
        except Exception:
            # Se a medicao falhar, mantem os defaults da classe.
            self.cursor_width = self.char_width
            self.cursor_height = max(2, self.char_height // 4)

        # opcoes_do_texto e opcoes_da_janela como atributos de instancia,
        # ja com os valores corretos depois de medir a fonte.
        self.opcoes_do_texto = {
            "font": self.fonte,
            "anchor": tk.NW,
            "fill": self.TEXT_COLOR_DEFAULT,
        }
        self.opcoes_da_janela = {
            "width": self.qtd_colunas * self.char_width + 5,
            "height": self.qtd_linhas * self.char_height + 2,
            "bd": 0,
            "bg": self.BACK_GROUND_COLOR_DEFAULT,
            "takefocus": 1,
            "highlightthickness": 0,
        }

        self.canvas = tk.Canvas(self.window, **self.opcoes_da_janela)
        self.canvas.focus_set()
        # _keys_down: conjunto de keycodes atualmente pressionados.
        # Usado pelo modo "polling" (is_key_pressed) para informar
        # corretamente se ha uma tecla pressionada AGORA, independente
        # do autorepeat do SO.
        self._keys_down = set()
        # Detectar X11: nele, autorepeat gera pares fake KeyRelease+KeyPress
        # com mesmo timestamp; em Windows/macOS o release so vem ao soltar.
        try:
            self._is_x11 = (self.window.tk.call('tk', 'windowingsystem') == 'x11')
        except Exception:
            self._is_x11 = False
        # Guarda o ultimo KeyRelease para detectar autorepeat no X11.
        self._pending_release = None
        self.window.bind("<Key>", self.on_key_pressed)
        self.window.bind("<KeyRelease>", self.on_key_released)
        # Quando a janela perde o foco, esquecer todas as teclas
        # pressionadas (senao podem "travar" como pressionadas).
        self.window.bind("<FocusOut>", self._on_focus_out)
        self.canvas.pack()
        self.set_key_released()

        # Pinta a tela inicial (preta, com cursor na pos 1,1).
        self.clr_scr()

    ###  metodos referentes a janela Canvas: paint() ###

    def paint(self):
        self.canvas.delete("all")
        for linha in range(self.qtd_linhas):
            z = linha * self.qtd_colunas
            self.canvas.create_text(
                2, linha * self.char_height,
                text=self.conteudo[z:z + self.qtd_colunas],
                **self.opcoes_do_texto)

        # So desenha o cursor se ele esta ligado E visivel no ciclo do blink.
        # No modo normal (fora de typing_text), cursor_blink_visible fica True
        # o tempo todo, entao se comporta como antes.
        if self.cursor_on and self.cursor_blink_visible:
            x = (self.cursor_X - 1) * self.char_width + 2
            y = (self.cursor_Y) * self.char_height - self.cursor_height

            if self.cursor_insert:
                self.canvas.create_rectangle(
                    x, y,
                    x + self.cursor_width, y + self.cursor_height,
                    fill=self.cursor_color, outline=self.cursor_color)
            else:
                # cursor "block" (modo overwrite)
                self.canvas.create_rectangle(
                    x, y - self.char_height + self.cursor_height * 2 - 2,
                    x + self.cursor_width, y + self.cursor_height,
                    fill=self.cursor_color, outline=self.cursor_color)

        self.canvas.update_idletasks()

    ###  metodos referente ao cursor de impressao  ###

    def goto_xy(self, x=0, y=0):
        if (x < 1) or (x > self.qtd_colunas):
            x = 1
            y = 1
        if (y < 1) or (y > self.qtd_linhas):
            x = 1
            y = 1
        self.cursor_X = x
        self.cursor_Y = y

    def set_cursor_on(self):
        self.cursor_on = True

    def set_cursor_off(self):
        self.cursor_on = False

    def set_cursor_mode(self, mode=True):
        self.cursor_on = mode

    def get_cursor_mode(self):
        return self.cursor_on

    def get_cursor_X(self):
        return self.cursor_X

    def get_cursor_Y(self):
        return self.cursor_Y

    def change_cursor_state(self):
        # Mantido por compat: alterna cursor_on (estado "ligado").
        self.cursor_on = not self.cursor_on

    def show_cursor(self):
        self.paint()

    def blinking_cursor(self):
        # Em vez de mexer em cursor_on (que e o "ligado/desligado" oficial),
        # mexemos so na flag de visibilidade do blink. Assim o paint() e
        # codigos externos que checam cursor_on nao se confundem.
        self.cursor_blink_visible = not self.cursor_blink_visible
        self.paint()
        self.cursor_blinking_after = self.canvas.after(
            self.cursor_ticks, self.blinking_cursor)

    def _start_blink(self):
        self._stop_blink()
        self.cursor_blink_visible = True
        self.cursor_blinking_after = self.canvas.after(
            self.cursor_ticks, self.blinking_cursor)

    def _stop_blink(self):
        if self.cursor_blinking_after is not None:
            try:
                self.canvas.after_cancel(self.cursor_blinking_after)
            except Exception:
                pass
            self.cursor_blinking_after = None
        self.cursor_blink_visible = True  # garante que o cursor "para visivel"

    ###  metodos de insercao de conteudo  ###

    def insert_text_xy_in_content(self, x=1, y=1, texto=''):
        x -= 1
        y -= 1
        pos_i = y * self.qtd_colunas + x
        if pos_i < 0:
            pos_i = 0
        # Filtra CR; quebras explicitas \n sao tratadas em printing_text.
        texto = texto.replace(chr(13), '')
        tam = len(texto)
        pos_f = pos_i + tam
        self.conteudo = self.conteudo[:pos_i] + texto + self.conteudo[pos_f:]
        y = pos_f // self.qtd_colunas + 1
        x = pos_f % self.qtd_colunas + 1
        return x, y

    def zero_content(self):
        self.conteudo = ' ' * self.qtd_colunas * self.qtd_linhas

    def insert_xy_to_eol(self, x=1, y=1, char=' ', qtd=0):
        texto = char * (self.qtd_colunas - x + 1)
        self.insert_text_xy_in_content(x, y, texto)

    def _scroll_up_one_line(self):
        """Empurra todas as linhas para cima e abre uma linha em branco
        no final (comportamento de terminal de verdade)."""
        self.conteudo = (
            self.conteudo[self.qtd_colunas:]
            + ' ' * self.qtd_colunas
        )

    def carriage_return_line_feed(self):
        self.cursor_X = 1
        self.cursor_Y += 1
        if self.cursor_Y > self.qtd_linhas:
            self._scroll_up_one_line()
            self.cursor_Y = self.qtd_linhas

    ###  metodos referente a tela: clrScr (apagar a tela toda)   ###

    def clr_scr(self):
        self.zero_content()
        self.goto_xy(1, 1)
        self.paint()

    def clr_eol(self):
        x = self.get_cursor_X()
        y = self.get_cursor_Y()
        self.insert_xy_to_eol(x=x, y=y)
        self.goto_xy(x, y)
        self.paint()

    ###  metodos de mudanca de cores da tela   ###

    def reset_colors(self):
        # CORRIGIDO: usar self. para acessar atributos da classe/instancia.
        self.opcoes_do_texto["fill"] = self.TEXT_COLOR_DEFAULT
        try:
            self.canvas.configure(bg=self.BACK_GROUND_COLOR_DEFAULT)
        except Exception:
            pass
        self.paint()

    def set_back_ground_color(self, back_ground_color=None):
        if back_ground_color is None:
            back_ground_color = self.BACK_GROUND_COLOR_DEFAULT
        # CORRIGIDO: realmente configura o fundo do canvas.
        try:
            self.canvas.configure(bg=back_ground_color)
        except Exception:
            pass
        self.paint()

    def set_text_color(self, text_color=None):
        if text_color is None:
            text_color = self.TEXT_COLOR_DEFAULT
        # CORRIGIDO: self.opcoes_do_texto em vez de variavel livre.
        self.opcoes_do_texto["fill"] = text_color
        self.paint()

    ###  metodos de impressao na tela   ###

    def printing_text(self, texto=None):
        # Aceita 0 / "" / etc., mas ignora None.
        if texto is None:
            return

        texto = str(texto)
        texto = texto.replace(chr(13), '')

        # Trata \n como CRLF (estilo terminal).
        if '\n' in texto:
            partes = texto.split('\n')
            for i, parte in enumerate(partes):
                if parte:
                    self._printing_chunk(parte)
                if i < len(partes) - 1:
                    self.carriage_return_line_feed()
            self.paint()
            return

        self._printing_chunk(texto)
        self.paint()

    def _printing_chunk(self, texto):
        """Insere um pedaco de texto SEM quebras de linha, fazendo scroll
        se necessario."""
        if not texto:
            return

        # Quantos caracteres cabem da posicao atual ate o fim da tela.
        x = self.get_cursor_X()
        y = self.get_cursor_Y()
        pos_atual = (y - 1) * self.qtd_colunas + (x - 1)
        cabem = self.qtd_chars - pos_atual

        if len(texto) <= cabem:
            new_x, new_y = self.insert_text_xy_in_content(x, y, texto)
            self.cursor_X = new_x
            self.cursor_Y = new_y
            # Se aterrissou exatamente em (1, qtd_linhas+1), prende na
            # ultima linha sem rolar (so rola quando algo NOVO for escrito).
            if self.cursor_Y > self.qtd_linhas:
                self.cursor_Y = self.qtd_linhas
                self.cursor_X = self.qtd_colunas + 1
                # CORRIGIDO: o buffer pode ter crescido se pos_f bateu
                # exatamente no limite — garante o tamanho certo.
                self.conteudo = self.conteudo[:self.qtd_chars]
        else:
            # Texto maior que o espaco restante: imprime o que cabe,
            # rola, imprime o resto, recursivamente.
            self.insert_text_xy_in_content(x, y, texto[:cabem])
            self.conteudo = self.conteudo[:self.qtd_chars]
            self._scroll_up_one_line()
            self.cursor_X = 1
            self.cursor_Y = self.qtd_linhas
            self._printing_chunk(texto[cabem:])

    def text(self, *args):
        for texto in args:
            self.printing_text(texto)

    def textln(self, *args):
        for texto in args:
            self.printing_text(texto)
        self.carriage_return_line_feed()
        self.paint()

    ###  metodo de temporizacao  ###

    def delay(self, milliseconds=0):
        # CORRIGIDO: window.after(ms) sem callback nao bloqueia — apenas
        # agenda nada. Aqui implementamos espera real processando eventos
        # da janela no meio tempo (para manter responsiva e para que
        # callbacks "after" cheguem a rodar).
        if milliseconds <= 0:
            self.window.update()
            return
        end = time.time() + milliseconds / 1000.0
        while True:
            now = time.time()
            if now >= end:
                break
            self.window.update()
            restante = end - now
            time.sleep(min(0.01, restante))

    ###  metodos referente a leitura de teclados  ###

    def run_key_pressed(self, event=None):
        # Hook a ser sobrescrito pelo usuario; mais defensivo que a versao
        # original (usa repr, nao falha se key_pressed for None).
        print("tecla_pressionada =", repr(self.key_pressed),
              self.code_key_pressed, self.is_key_pressed(),
              " - ", getattr(event, 'char', ''))

    def set_key_released(self):
        self.key_pressed = None
        self.code_key_pressed = None

    def get_key_pressed(self):
        return self.key_pressed

    def get_key_code_pressed(self):
        return self.code_key_pressed

    def on_key_pressed(self, event):
        # No X11, se acabamos de receber um KeyRelease com o mesmo
        # keycode no mesmo timestamp, esse e o "fake release" do
        # autorepeat — cancelar a remocao.
        if self._pending_release is not None:
            prev_code, prev_time = self._pending_release
            if (self._is_x11
                    and prev_code == event.keycode
                    and prev_time == event.time):
                # Era autorepeat: reverter a "soltura" — a tecla NUNCA
                # foi solta, na verdade.
                self._keys_down.add(prev_code)
            self._pending_release = None

        self.key_pressed = event.char
        self.code_key_pressed = event.keycode
        if event.keycode:
            self._keys_down.add(event.keycode)
        # Se typing_text esta esperando uma tecla, acorda o wait_variable.
        if self._typing_key_var is not None:
            self._typing_key_var.set(self._typing_key_var.get() + 1)

    def on_key_released(self, event):
        if self._is_x11:
            # No X11, agendamos a remocao para o proximo ciclo do event
            # loop: se vier um KeyPress no mesmo instante, e autorepeat
            # e desfazemos a remocao. Aqui apenas removemos do conjunto
            # e guardamos a info; on_key_pressed verifica em seguida.
            if event.keycode in self._keys_down:
                self._keys_down.discard(event.keycode)
            self._pending_release = (event.keycode, event.time)
            # Limpa key_pressed/code apenas se nao for "autorepeat"
            # (resolvido na proxima chamada de on_key_pressed). Aqui ja
            # zeramos: read_key le esse estado e o re-set acontece no
            # proximo KeyPress se for autorepeat. Para o polling
            # (is_key_pressed) o que importa e _keys_down.
            self.set_key_released()
        else:
            # Windows / macOS: KeyRelease so vem ao soltar de verdade.
            self._keys_down.discard(event.keycode)
            self._pending_release = None
            self.set_key_released()

    def _on_focus_out(self, event):
        # Esquece todas as teclas para nao "travarem" como pressionadas.
        self._keys_down.clear()
        self._pending_release = None
        self.set_key_released()

    def is_key_pressed(self):
        # Forca o Tk a processar eventos pendentes antes de consultar o
        # estado. Sem isto, num laco apertado (ex.: for ...: text("X"))
        # o callback de tecla nunca seria chamado e is_key_pressed()
        # retornaria sempre False.
        try:
            self.window.update()
        except Exception:
            pass
        return bool(self._keys_down)

    def read_key(self):
        # CORRIGIDO: nao faz mais busy-loop a 100% de CPU.
        # Espera ate uma tecla soltar (caso ja estivesse pressionada) e depois
        # ate uma nova tecla chegar, dando time.sleep no meio.
        while self.is_key_pressed():
            self.canvas.update()
            time.sleep(0.01)
        while not self.is_key_pressed():
            self.canvas.update()
            time.sleep(0.01)
        return self.key_pressed

    def typing_text(self):
        """Le uma linha de texto da tecla do usuario, com cursor piscando."""

        def insert_str(string, str_to_insert, index, insert=True):
            return (string[:index] + str_to_insert
                    + string[(index if insert else index + len(str_to_insert)):])

        def delete_char_at(string, index):
            return string[:index] + string[(index + 1):]

        s = ""
        x_cursor_inicial = self.get_cursor_X()
        y_cursor_inicial = self.get_cursor_Y()
        index_string = 0
        cursor_mode = self.get_cursor_mode()
        self.cursor_XOR_mode = True
        self.set_cursor_on()
        self.cursor_typing_text = True

        # Variavel Tk que sera "setada" toda vez que uma tecla chegar.
        # Usamos wait_variable em vez de busy-loop — isso libera a event loop
        # do Tk para chamar o `after` do blink, fazendo o cursor piscar de
        # verdade.
        self._typing_key_var = tk.IntVar(master=self.window, value=0)

        # Comeca o blink (so para no fim da funcao).
        self._start_blink()

        try:
            while True:
                self.set_key_released()

                # Espera ate uma tecla chegar (event-driven, nao busy-loop).
                # Enquanto isso, o Tk processa o after do blink normalmente.
                current_val = self._typing_key_var.get()
                while self._typing_key_var.get() == current_val:
                    self.window.wait_variable(self._typing_key_var)

                c = self.key_pressed if self.key_pressed is not None else ""
                ord_tecla = self.code_key_pressed

                if (len(s) < 256 and len(c) > 0):
                    if (c >= " " and c <= chr(126)):
                        if (self.cursor_insert or (index_string == len(s))):
                            s = insert_str(s, c, index_string)
                        else:
                            s = insert_str(s, c, index_string, False)
                        index_string += 1

                if ord_tecla == 37:    # VK_LEFT
                    index_string -= 1
                if ord_tecla == 39:    # VK_RIGHT
                    index_string += 1
                if ord_tecla == 8:     # VK_BACKSPACE
                    if index_string > 0:
                        s = delete_char_at(s, index_string - 1)
                        index_string -= 1
                if ord_tecla == 46:    # VK_DEL
                    if index_string < len(s):
                        s = delete_char_at(s, index_string)
                if ord_tecla == 36:    # VK_HOME
                    index_string = 0
                if ord_tecla == 35:    # VK_END
                    index_string = len(s)
                if ord_tecla == 45:    # VK_INSERT
                    self.cursor_insert = not self.cursor_insert

                if index_string < 0:
                    index_string = 0
                if index_string > len(s):
                    index_string = len(s)

                # Reimprime a string toda na posicao inicial. Importante:
                # paramos o blink antes para garantir que o cursor visivel
                # nao "vaze" durante a reimpressao.
                self._stop_blink()
                self.set_cursor_off()
                self.goto_xy(x_cursor_inicial, y_cursor_inicial)
                self.text(s)

                if (ord_tecla == 8) or (ord_tecla == 46):
                    self.text(" ")

                x_cursor = 1 + (x_cursor_inicial + index_string - 1) % self.qtd_colunas
                y_cursor = y_cursor_inicial + int(
                    (index_string - 1 + x_cursor_inicial) / self.qtd_colunas)
                if y_cursor > self.qtd_linhas:
                    y_cursor_inicial -= 1
                    y_cursor -= 1

                self.set_cursor_on()
                self.goto_xy(x_cursor, y_cursor)

                if ord_tecla == 13:    # ENTER -> sai do laco
                    self.show_cursor()
                    break

                # Reinicia o blink na nova posicao do cursor.
                self._start_blink()

        finally:
            self._stop_blink()
            self._typing_key_var = None
            self.set_cursor_mode(cursor_mode)
            self.cursor_typing_text = False
            self.cursor_XOR_mode = False
            self.cursor_insert = True

        return s

    def type_textln(self, *args):
        self.textln(*args)
        texto = self.type_text()
        self.carriage_return_line_feed()
        return texto

    def type_text(self, *args):
        self.text(*args)
        return self.typing_text()

    def typeTextln(self, *args):
        # Mantido por compat. com a API antiga. (Note: no original esta
        # funcao tinha um `print(args)` de debug; removido aqui.)
        texto = self.type_text()
        self.carriage_return_line_feed()
        return texto


"""
 *  Falta fazer ainda:
 *
 *  1- expor o nivel de "auto-repeat" do teclado (atualmente depende do SO).
 *  2- permitir cores por caractere (foreground/background no buffer).
 *  3- API para esconder/mostrar a janela.
"""

pytme = Pytme()
goto_xy = pytme.goto_xy
set_cursor_on = pytme.set_cursor_on
set_cursor_off = pytme.set_cursor_off
set_cursor_mode = pytme.set_cursor_mode
get_cursor_mode = pytme.get_cursor_mode
get_cursor_X = pytme.get_cursor_X
get_cursor_Y = pytme.get_cursor_Y
change_cursor_state = pytme.change_cursor_state
show_cursor = pytme.show_cursor

insert_xy_to_eol = pytme.insert_xy_to_eol
carriage_return_line_feed = pytme.carriage_return_line_feed
clr_scr = pytme.clr_scr
clr_eol = pytme.clr_eol

reset_colors = pytme.reset_colors
set_back_ground_color = pytme.set_back_ground_color
set_text_color = pytme.set_text_color

text = pytme.text
textln = pytme.textln
set_key_released = pytme.set_key_released
get_key_pressed = pytme.get_key_pressed
get_key_code_pressed = pytme.get_key_code_pressed
on_key_pressed = pytme.on_key_pressed
on_key_released = pytme.on_key_released

delay = pytme.delay

is_key_pressed = pytme.is_key_pressed
read_key = pytme.read_key
type_textln = pytme.type_textln
type_text = pytme.type_text
typeTextln = pytme.typeTextln
