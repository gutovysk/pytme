"""
    APFJogos - Python Text Mode Emulator (port do JTME para Python)
        versao: 2.1 (paridade de API com PyTME)
        data: 2026

    Esta e uma reimplementacao do JTME (Java Text Mode Emulator) em
    Python, preservando a API snake_case do PyTME para compatibilidade
    com programas existentes.

    Estilo de uso (igual ao JTME, com nomes do PyTME):

        Jtme.text("ola mundo")
        Jtme.textln(" - linha 1")
        Jtme.delay(500)
        nome = Jtme.type_text("Seu nome: ")

    Ou via importacao direta:

        from Jtme import *
        text("ola mundo")
        delay(500)

    As principais funcoes sao:
        clr_scr(); clr_eol();
        text(...); textln(...);
        is_key_pressed(); read_key(); type_text(); type_textln();
        goto_xy(x, y); delay(ms);
        set_cursor_on(); set_cursor_off();
        set_text_color(cor); set_back_ground_color(cor); reset_colors();

    Diferencas em relacao ao JTME original:
      - Tudo em Python/Tk (em vez de Java/Swing).
      - API com snake_case (mesma do PyTME).
      - Inicializacao preguicosa: a janela so e criada na primeira
        chamada (igual ao JTME).
      - Bugs do JTME corrigidos:
        * readKey() do JTME tinha busy-loop a 100% de CPU; aqui usa
          espera com pequeno sleep.
        * setBackGroundColor mudava o JFrame mas nao o conteudo; aqui
          configura o canvas corretamente.
      - Melhorias herdadas do PyTME:
        * carriage_return_line_feed faz scroll real (terminal).
        * delay() bloqueia de verdade e processa eventos.
        * is_key_pressed informa "tecla pressionada AGORA" (com filtro
          de autorepeat no X11).
        * Cursor pisca corretamente em type_text via wait_variable.

    Conceito de design herdado do JTME: a classe e usada como
    "singleton estatico" — voce nao precisa instancia-la. Os metodos
    sao classmethods e o estado fica na propria classe.
"""

try:
    import Tkinter as _tk
    import tkFont as _tkFont
    _Font = _tkFont.Font
except ImportError:
    import tkinter as _tk
    from tkinter.font import Font as _Font

import time as _time


class Jtme(object):
    # =============================================================
    # configuracao da tela (atributos de classe, como no JTME)
    # =============================================================
    _f = None                    # janela Tk (None = nao inicializada)
    _canvas = None               # canvas de desenho
    _titulo = "APFJogos - Python Text Mode Emulator (port do JTME)"

    qtd_colunas = 80
    qtd_linhas = 25
    font_size = 13
    fonte = ('Courier', 13, 'bold')
    char_width = 10              # recalculado em _init()
    char_height = 16             # recalculado em _init()
    width = 0
    height = 0
    BACK_GROUND_COLOR_DEFAULT = "BLACK"
    TEXT_COLOR_DEFAULT = "WHITE"

    # conteudo: matriz qtd_linhas x qtd_colunas de caracteres
    # (igual ao Java: char[][] conteudo)
    _conteudo = None             # criado em _init()

    # --- cursor ---
    cursor_X = 1
    cursor_Y = 1
    cursor_color = "WHITE"
    cursor_on = True             # True = cursor visivel quando nao piscando
    cursor_blink_visible = True  # estado atual do blink (flag separada)
    cursor_insert = True         # True = modo INSERT, False = OVERWRITE
    cursor_typing_text = False   # True durante type_text
    cursor_XOR_mode = True       # mantido por compatibilidade
    cursor_ticks = 500           # ms entre piscadas
    _blink_after_id = None       # id do timer atual do blink

    # --- teclado ---
    key_pressed = None           # ultima tecla recebida (event.char)
    code_key_pressed = -1        # ultimo keycode recebido

    # _keys_down: conjunto de keycodes ATUALMENTE pressionados.
    # Usado por is_key_pressed para detectar "tem tecla apertada agora",
    # independente de autorepeat do SO.
    _keys_down = None

    # filtro de autorepeat no X11
    _is_x11 = False
    _pending_release = None

    # variavel Tk usada pelo type_text para acordar do wait_variable
    _typing_key_var = None

    # =============================================================
    # inicializacao da janela (lazy)
    # =============================================================

    @classmethod
    def _ensure_init(cls):
        """Inicializa a janela na primeira chamada (igual `if (f==null) init()` do JTME)."""
        if cls._f is not None:
            return
        cls._init()

    @classmethod
    def _init(cls):
        cls._f = _tk.Tk()
        cls._f.resizable(width=False, height=False)
        cls._f.title(cls._titulo)

        # mede a fonte real para nao chutar 8x12
        try:
            f = _Font(family=cls.fonte[0], size=int(cls.fonte[1]),
                      weight=cls.fonte[2] if len(cls.fonte) > 2 else 'normal')
            mw = f.measure('M')
            mh = f.metrics('linespace')
            if mw > 0:
                cls.char_width = mw
            if mh > 0:
                cls.char_height = mh
        except Exception:
            pass

        cls.cursor_width = cls.char_width
        cls.cursor_height = max(2, cls.char_height // 4)

        cls.width = cls.qtd_colunas * cls.char_width + 5
        cls.height = cls.qtd_linhas * cls.char_height + 2

        cls._opcoes_do_texto = {
            "font": cls.fonte,
            "anchor": _tk.NW,
            "fill": cls.TEXT_COLOR_DEFAULT,
        }

        cls._canvas = _tk.Canvas(
            cls._f, width=cls.width, height=cls.height,
            bd=0, bg=cls.BACK_GROUND_COLOR_DEFAULT,
            takefocus=1, highlightthickness=0,
        )
        cls._canvas.focus_set()
        cls._canvas.pack()

        # detecta X11 para tratamento de autorepeat
        try:
            cls._is_x11 = (cls._f.tk.call('tk', 'windowingsystem') == 'x11')
        except Exception:
            cls._is_x11 = False

        cls._keys_down = set()
        cls._pending_release = None

        # cria a matriz 2D de conteudo (qtd_linhas x qtd_colunas), igual ao Java
        cls._conteudo = [[' '] * cls.qtd_colunas for _ in range(cls.qtd_linhas)]

        cls._f.bind("<Key>", cls._on_key_pressed)
        cls._f.bind("<KeyRelease>", cls._on_key_released)
        cls._f.bind("<FocusOut>", cls._on_focus_out)

        cls._set_key_released()
        cls.clr_scr()

    # =============================================================
    # paint: desenha a tela inteira
    # =============================================================

    @classmethod
    def _paint(cls):
        cls._canvas.delete("all")
        for linha in range(cls.qtd_linhas):
            cls._canvas.create_text(
                2, linha * cls.char_height,
                text=''.join(cls._conteudo[linha]),
                **cls._opcoes_do_texto
            )

        # cursor (so se ligado E visivel no ciclo do blink)
        if cls.cursor_on and cls.cursor_blink_visible:
            x = (cls.cursor_X - 1) * cls.char_width + 2
            y = cls.cursor_Y * cls.char_height - cls.cursor_height
            if cls.cursor_insert:
                cls._canvas.create_rectangle(
                    x, y, x + cls.cursor_width, y + cls.cursor_height,
                    fill=cls.cursor_color, outline=cls.cursor_color)
            else:
                cls._canvas.create_rectangle(
                    x, y - cls.char_height + cls.cursor_height * 2 - 2,
                    x + cls.cursor_width, y + cls.cursor_height,
                    fill=cls.cursor_color, outline=cls.cursor_color)

        cls._canvas.update_idletasks()

    # =============================================================
    # cursor: gotoXY, on/off, modo, posicao
    # =============================================================

    @classmethod
    def goto_xy(cls, x=1, y=1):
        cls._ensure_init()
        if (x < 1) or (x > cls.qtd_colunas):
            x, y = 1, 1
        if (y < 1) or (y > cls.qtd_linhas):
            x, y = 1, 1
        cls.cursor_X = x
        cls.cursor_Y = y
        cls._paint()

    @classmethod
    def set_cursor_on(cls):
        cls._ensure_init()
        cls.cursor_on = True
        cls._paint()

    @classmethod
    def set_cursor_off(cls):
        cls._ensure_init()
        cls.cursor_on = False
        cls._paint()

    @classmethod
    def set_cursor_mode(cls, mode=True):
        cls._ensure_init()
        cls.cursor_on = mode
        cls._paint()

    @classmethod
    def get_cursor_mode(cls):
        return cls.cursor_on

    @classmethod
    def get_cursor_X(cls):
        return cls.cursor_X

    @classmethod
    def get_cursor_Y(cls):
        return cls.cursor_Y

    @classmethod
    def show_cursor(cls):
        cls._ensure_init()
        cls._paint()

    # --- blink (mecanica interna) ---
    @classmethod
    def _blink_step(cls):
        cls.cursor_blink_visible = not cls.cursor_blink_visible
        cls._paint()
        cls._blink_after_id = cls._canvas.after(
            cls.cursor_ticks, cls._blink_step)

    @classmethod
    def _start_blink(cls):
        cls._stop_blink()
        cls.cursor_blink_visible = True
        cls._blink_after_id = cls._canvas.after(
            cls.cursor_ticks, cls._blink_step)

    @classmethod
    def _stop_blink(cls):
        if cls._blink_after_id is not None:
            try:
                cls._canvas.after_cancel(cls._blink_after_id)
            except Exception:
                pass
            cls._blink_after_id = None
        cls.cursor_blink_visible = True

    # =============================================================
    # manipulacao do buffer de conteudo (estilo JTME, matriz 2D)
    # =============================================================

    @classmethod
    def _zero_conteudo(cls):
        for linha in range(cls.qtd_linhas):
            for coluna in range(cls.qtd_colunas):
                cls._conteudo[linha][coluna] = ' '

    @classmethod
    def _insert_line_up(cls, linha):
        """Rola as linhas de 0..linha-1 uma posicao pra cima e zera a
        ultima. Equivalente ao InsertLineUp do JTME — usado para scroll."""
        # OBS: parametro linha e 1-based (como no Java).
        for i in range(1, linha):
            for j in range(cls.qtd_colunas):
                cls._conteudo[i - 1][j] = cls._conteudo[i][j]
        for j in range(cls.qtd_colunas):
            cls._conteudo[linha - 1][j] = ' '

    @classmethod
    def _carriage_return_line_feed(cls):
        cls.cursor_X = 1
        cls.cursor_Y += 1
        if cls.cursor_Y > cls.qtd_linhas:
            cls._insert_line_up(cls.qtd_linhas)
            cls.cursor_Y = cls.qtd_linhas

    # =====================================================
    # API publica equivalente ao PyTME (compatibilidade)
    # =====================================================

    @classmethod
    def carriage_return_line_feed(cls):
        """Quebra de linha (vai para coluna 1 da proxima linha). Se ja
        estiver na ultima linha, faz scroll para cima."""
        cls._ensure_init()
        cls._carriage_return_line_feed()
        cls._paint()

    @classmethod
    def change_cursor_state(cls):
        """Alterna o estado do cursor (ligado <-> desligado)."""
        cls._ensure_init()
        cls.cursor_on = not cls.cursor_on
        cls._paint()

    @classmethod
    def insert_xy_to_eol(cls, x=1, y=1, char=' ', qtd=0):
        """Preenche da posicao (x,y) ate o fim da linha com o caractere
        dado. O parametro 'qtd' existe por compatibilidade com PyTME mas
        nao e usado."""
        cls._ensure_init()
        if y < 1 or y > cls.qtd_linhas:
            return
        if x < 1:
            x = 1
        if x > cls.qtd_colunas:
            return
        c = char[0] if char else ' '
        for col in range(x - 1, cls.qtd_colunas):
            cls._conteudo[y - 1][col] = c
        cls._paint()

    @classmethod
    def insert_text_xy_in_content(cls, x=1, y=1, texto=''):
        """Insere texto em (x,y) sem mover o cursor "logico" do usuario.
        Retorna (novo_x, novo_y) onde o cursor PARARIA se este texto
        fosse impresso (mas o cursor real nao e movido)."""
        cls._ensure_init()
        if y < 1 or y > cls.qtd_linhas:
            return x, y
        # filtra CR (igual a' impressao normal)
        texto = str(texto).replace('\r', '')
        pos_x = x - 1
        pos_y = y - 1
        for ch in texto:
            if ch == '\n':
                pos_x = 0
                pos_y += 1
                if pos_y >= cls.qtd_linhas:
                    pos_y = cls.qtd_linhas - 1
                continue
            if 0 <= pos_x < cls.qtd_colunas and 0 <= pos_y < cls.qtd_linhas:
                cls._conteudo[pos_y][pos_x] = ch
            pos_x += 1
            if pos_x >= cls.qtd_colunas:
                pos_x = 0
                pos_y += 1
                if pos_y >= cls.qtd_linhas:
                    pos_y = cls.qtd_linhas - 1
        cls._paint()
        return pos_x + 1, pos_y + 1

    @classmethod
    def paint(cls):
        """Forca o redesenho da tela. Igual ao paint() do PyTME."""
        cls._ensure_init()
        cls._paint()

    @classmethod
    def printing_text(cls, texto=None):
        """Imprime um texto na posicao atual do cursor (equivalente ao
        printing_text do PyTME). Em geral use text() em vez desta."""
        cls._ensure_init()
        cls.text(texto)

    @classmethod
    def zero_content(cls):
        """Zera (preenche com espacos) o conteudo da tela sem repintar."""
        cls._ensure_init()
        cls._zero_conteudo()

    @classmethod
    def blinking_cursor(cls):
        """Faz o cursor piscar uma vez (alterna visibilidade do blink e
        agenda a proxima). Em geral o blink e' gerenciado automaticamente
        durante type_text."""
        cls._ensure_init()
        cls._blink_step()

    @classmethod
    def on_key_pressed(cls, event):
        """Handler interno para eventos de KeyPress. Exposto para
        compatibilidade com PyTME."""
        cls._on_key_pressed(event)

    @classmethod
    def on_key_released(cls, event):
        """Handler interno para eventos de KeyRelease. Exposto para
        compatibilidade com PyTME."""
        cls._on_key_released(event)

    @classmethod
    def typing_text(cls):
        """Le uma linha de texto da tecla do usuario, com cursor piscando.
        Retorna a string digitada. Em geral use type_text(prompt) em vez."""
        cls._ensure_init()
        return cls._typing_text()

    @classmethod
    def run_key_pressed(cls, event=None):
        """Hook que pode ser sobrescrito pelo usuario para reagir a teclas.
        Versao padrao apenas imprime info de debug no terminal."""
        print("tecla_pressionada =", repr(cls.key_pressed),
              cls.code_key_pressed, cls.is_key_pressed(),
              " - ", getattr(event, 'char', ''))

    @classmethod
    def typeTextln(cls, *args):
        """Alias camelCase de type_textln (compatibilidade com versao antiga)."""
        return cls.type_textln(*args)

    # =============================================================
    # apagar tela / linha
    # =============================================================

    @classmethod
    def clr_scr(cls):
        cls._ensure_init()
        cls._zero_conteudo()
        cls.cursor_X = 1
        cls.cursor_Y = 1
        cls._paint()

    @classmethod
    def clr_eol(cls):
        cls._ensure_init()
        linha = cls.cursor_Y - 1
        for coluna in range(cls.cursor_X - 1, cls.qtd_colunas):
            cls._conteudo[linha][coluna] = ' '
        cls._paint()

    # =============================================================
    # cores
    # =============================================================

    @classmethod
    def reset_colors(cls):
        cls._ensure_init()
        cls._opcoes_do_texto["fill"] = cls.TEXT_COLOR_DEFAULT
        try:
            cls._canvas.configure(bg=cls.BACK_GROUND_COLOR_DEFAULT)
        except Exception:
            pass
        cls._paint()

    @classmethod
    def set_back_ground_color(cls, back_ground_color=None):
        cls._ensure_init()
        if back_ground_color is None:
            back_ground_color = cls.BACK_GROUND_COLOR_DEFAULT
        try:
            cls._canvas.configure(bg=back_ground_color)
        except Exception:
            pass
        cls._paint()

    @classmethod
    def set_text_color(cls, text_color=None):
        cls._ensure_init()
        if text_color is None:
            text_color = cls.TEXT_COLOR_DEFAULT
        cls._opcoes_do_texto["fill"] = text_color
        cls._paint()

    # =============================================================
    # impressao
    # =============================================================

    @classmethod
    def text(cls, *args):
        """Imprime um ou mais argumentos concatenados, na posicao atual do cursor."""
        cls._ensure_init()
        if not args:
            cls._paint()
            return
        s = ''.join(str(a) for a in args if a is not None)
        # filtra CR; trata \n como CRLF
        s = s.replace('\r', '')
        for ch in s:
            if ch == '\n':
                cls._carriage_return_line_feed()
                continue
            cls._conteudo[cls.cursor_Y - 1][cls.cursor_X - 1] = ch
            cls.cursor_X += 1
            if cls.cursor_X > cls.qtd_colunas:
                cls._carriage_return_line_feed()
        cls._paint()

    @classmethod
    def textln(cls, *args):
        """Imprime e quebra linha. Igual a print() seguido de \\n no Java."""
        cls._ensure_init()
        if args:
            cls.text(*args)
        cls._carriage_return_line_feed()
        cls._paint()

    # =============================================================
    # delay
    # =============================================================

    @classmethod
    def delay(cls, milliseconds=0):
        """Espera por X ms. Equivalente ao Thread.sleep do Java, mas
        processando eventos da janela no meio tempo para manter
        responsivo e para callbacks 'after' poderem rodar."""
        cls._ensure_init()
        if milliseconds <= 0:
            cls._f.update()
            return
        end = _time.time() + milliseconds / 1000.0
        while True:
            now = _time.time()
            if now >= end:
                break
            cls._f.update()
            restante = end - now
            _time.sleep(min(0.01, restante))

    # =============================================================
    # teclado
    # =============================================================

    @classmethod
    def _set_key_released(cls):
        cls.key_pressed = None
        cls.code_key_pressed = -1

    @classmethod
    def set_key_released(cls):
        cls._set_key_released()

    @classmethod
    def get_key_pressed(cls):
        return cls.key_pressed

    @classmethod
    def get_key_code_pressed(cls):
        return cls.code_key_pressed

    @classmethod
    def _on_key_pressed(cls, event):
        # filtro de autorepeat no X11: KeyRelease + KeyPress de mesma tecla
        # no mesmo timestamp = autorepeat (a tecla NUNCA foi solta).
        if cls._pending_release is not None:
            prev_code, prev_time = cls._pending_release
            if (cls._is_x11
                    and prev_code == event.keycode
                    and prev_time == event.time):
                cls._keys_down.add(prev_code)
            cls._pending_release = None

        cls.key_pressed = event.char
        cls.code_key_pressed = event.keycode
        if event.keycode:
            cls._keys_down.add(event.keycode)
        if cls._typing_key_var is not None:
            cls._typing_key_var.set(cls._typing_key_var.get() + 1)

    @classmethod
    def _on_key_released(cls, event):
        if cls._is_x11:
            cls._keys_down.discard(event.keycode)
            cls._pending_release = (event.keycode, event.time)
        else:
            cls._keys_down.discard(event.keycode)
            cls._pending_release = None
        cls._set_key_released()

    @classmethod
    def _on_focus_out(cls, event):
        cls._keys_down.clear()
        cls._pending_release = None
        cls._set_key_released()

    @classmethod
    def is_key_pressed(cls):
        """Retorna True se ha uma tecla pressionada AGORA. Processa
        eventos pendentes antes de consultar — funciona dentro de
        laços apertados."""
        cls._ensure_init()
        try:
            cls._f.update()
        except Exception:
            pass
        return bool(cls._keys_down)

    @classmethod
    def read_key(cls):
        """Bloqueia ate uma tecla ser pressionada. Retorna o caractere.
        Aguarda primeiro que toda tecla atual seja solta, depois espera
        uma nova tecla."""
        cls._ensure_init()
        while cls._keys_down:
            cls._f.update()
            _time.sleep(0.01)
        while not cls._keys_down:
            cls._f.update()
            _time.sleep(0.01)
        return cls.key_pressed

    @classmethod
    def type_text(cls, *args):
        """Imprime opcionalmente um prompt e le uma linha de texto com
        cursor piscando. Retorna a string digitada (sem o Enter final)."""
        cls._ensure_init()
        if args:
            cls.text(*args)
        return cls._typing_text()

    @classmethod
    def type_textln(cls, *args):
        s = cls.type_text(*args)
        cls._carriage_return_line_feed()
        cls._paint()
        return s

    @classmethod
    def _typing_text(cls):
        def insert_str(string, ch, idx, insert=True):
            return (string[:idx] + ch
                    + string[(idx if insert else idx + len(ch)):])

        def delete_at(string, idx):
            return string[:idx] + string[(idx + 1):]

        s = ""
        x0 = cls.cursor_X
        y0 = cls.cursor_Y
        index_string = 0
        cursor_mode = cls.cursor_on
        cls.cursor_XOR_mode = True
        cls.cursor_on = True
        cls.cursor_typing_text = True

        cls._typing_key_var = _tk.IntVar(master=cls._f, value=0)
        cls._start_blink()

        try:
            while True:
                cls._set_key_released()

                # espera event-driven: deixa o Tk processar o blink
                cur = cls._typing_key_var.get()
                while cls._typing_key_var.get() == cur:
                    cls._f.wait_variable(cls._typing_key_var)

                c = cls.key_pressed if cls.key_pressed is not None else ""
                ord_tecla = cls.code_key_pressed

                if (len(s) < 256 and len(c) > 0):
                    if (c >= " " and c <= chr(126)):
                        if (cls.cursor_insert or (index_string == len(s))):
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
                        s = delete_at(s, index_string - 1)
                        index_string -= 1
                if ord_tecla == 46:    # VK_DEL
                    if index_string < len(s):
                        s = delete_at(s, index_string)
                if ord_tecla == 36:    # VK_HOME
                    index_string = 0
                if ord_tecla == 35:    # VK_END
                    index_string = len(s)
                if ord_tecla == 45:    # VK_INSERT
                    cls.cursor_insert = not cls.cursor_insert

                if index_string < 0:
                    index_string = 0
                if index_string > len(s):
                    index_string = len(s)

                # redesenha a string toda a partir da posicao inicial
                cls._stop_blink()
                cls.cursor_on = False
                cls.cursor_X, cls.cursor_Y = x0, y0
                cls.text(s)
                if ord_tecla == 8 or ord_tecla == 46:
                    cls.text(" ")

                # calcula posicao do cursor em funcao do index
                x_cursor = 1 + (x0 + index_string - 1) % cls.qtd_colunas
                y_cursor = y0 + (x0 + index_string - 1) // cls.qtd_colunas
                if y_cursor > cls.qtd_linhas:
                    y0 -= 1
                    y_cursor -= 1

                cls.cursor_on = True
                cls.cursor_X, cls.cursor_Y = x_cursor, y_cursor

                if ord_tecla == 13:    # ENTER
                    cls._paint()
                    break

                cls._start_blink()

        finally:
            cls._stop_blink()
            cls._typing_key_var = None
            cls.cursor_on = cursor_mode
            cls.cursor_typing_text = False
            cls.cursor_XOR_mode = False
            cls.cursor_insert = True

        return s


# =============================================================
# Aliases globais (mesma API do PyTME): permite usar
#   from Jtme import *
# sem precisar escrever "Jtme." na frente de cada chamada.
# =============================================================

goto_xy = Jtme.goto_xy
set_cursor_on = Jtme.set_cursor_on
set_cursor_off = Jtme.set_cursor_off
set_cursor_mode = Jtme.set_cursor_mode
get_cursor_mode = Jtme.get_cursor_mode
get_cursor_X = Jtme.get_cursor_X
get_cursor_Y = Jtme.get_cursor_Y
show_cursor = Jtme.show_cursor

clr_scr = Jtme.clr_scr
clr_eol = Jtme.clr_eol

reset_colors = Jtme.reset_colors
set_back_ground_color = Jtme.set_back_ground_color
set_text_color = Jtme.set_text_color

text = Jtme.text
textln = Jtme.textln

delay = Jtme.delay

set_key_released = Jtme.set_key_released
get_key_pressed = Jtme.get_key_pressed
get_key_code_pressed = Jtme.get_key_code_pressed
is_key_pressed = Jtme.is_key_pressed
read_key = Jtme.read_key
type_text = Jtme.type_text
type_textln = Jtme.type_textln

# Compatibilidade extra com a API do PyTME:
carriage_return_line_feed = Jtme.carriage_return_line_feed
change_cursor_state = Jtme.change_cursor_state
insert_xy_to_eol = Jtme.insert_xy_to_eol
insert_text_xy_in_content = Jtme.insert_text_xy_in_content
paint = Jtme.paint
printing_text = Jtme.printing_text
zero_content = Jtme.zero_content
blinking_cursor = Jtme.blinking_cursor
on_key_pressed = Jtme.on_key_pressed
on_key_released = Jtme.on_key_released
typing_text = Jtme.typing_text
run_key_pressed = Jtme.run_key_pressed
typeTextln = Jtme.typeTextln
