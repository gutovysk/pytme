"""
    APFJogos - PyTME (Python Text Mode Emulator)
        versao: 3.2 (fonte forcada monoespacada + cursor sempre visivel ao mover)
        data: 20/05/2026

    PyTME emula uma tela de modo texto 80x25 sobre Tk, com cursor
    piscante, leitura de teclado, cores, scroll, etc. Foi pensado
    para o livro "Aprenda a Programar Fazendo Jogos" como apoio
    didatico para escrever jogos e programas no estilo antigo.

    Estilo de uso:

        Pytme.text("ola mundo")
        Pytme.textln(" - linha 1")
        Pytme.delay(500)
        nome = Pytme.type_text("Seu nome: ")

    Ou via importacao direta (sem precisar do prefixo da classe):

        from PyTME import *
        text("ola mundo")
        delay(500)

    As principais funcoes sao:
        clr_scr(); clr_eol();
        text(...); textln(...);
        is_key_pressed(); read_key(); type_text(); type_textln();
        goto_xy(x, y); delay(ms);
        set_cursor_on(); set_cursor_off();
        set_text_color(cor); set_back_ground_color(cor); reset_colors();

    --- HISTORICO ---

    Esta versao do PyTME foi reescrita a partir do port em Python do
    JTME (Java Text Mode Emulator) do Carlos A. Correia, que foi
    chamado de "Pytme.py" durante o desenvolvimento. Apos a fase de
    port e estabilizacao, a biblioteca voltou ao nome original PyTME,
    ja que a implementacao agora e' nativa Python (e nao mais uma
    transcricao de Java).

    A linhagem completa:
      - PyTME 1.0 — versao original em Python.
      - Jtme.py (versoes 1.x e 2.x) — port em Python do JTME Java,
        com arquitetura mais limpa (classe singleton estatica, lazy
        init, scroll real, etc).
      - PyTME 3.0 — renomeacao do Pytme.py de volta para PyTME,
        consolidando a evolucao em uma biblioteca so.

    Bugs do JTME Java corrigidos durante o port:
      - readKey() tinha busy-loop a 100% de CPU; aqui usa espera com
        pequeno sleep.
      - setBackGroundColor mudava o JFrame mas nao o conteudo; aqui
        configura o canvas corretamente.

    Caracteristicas herdadas e melhoradas do PyTME original:
      - carriage_return_line_feed faz scroll real (estilo terminal).
      - delay() bloqueia de verdade e processa eventos.
      - is_key_pressed informa "tecla pressionada AGORA" (com filtro
        de autorepeat no X11) e mantem historico das teclas
        atualmente pressionadas para resposta rapida em jogos.
      - Cursor pisca corretamente em type_text via wait_variable.

    Conceito de design (heranca do JTME): a classe e usada como
    "singleton estatico" — voce nao precisa instancia-la. Os metodos
    sao classmethods e o estado fica na propria classe. A janela so
    e criada na primeira chamada (inicializacao preguicosa).
"""

try:
    import Tkinter as _tk
    import tkFont as _tkFont
    _Font = _tkFont.Font
except ImportError:
    import tkinter as _tk
    from tkinter.font import Font as _Font

import time as _time


class Pytme(object):
    # =============================================================
    # configuracao da tela (atributos de classe, como no JTME)
    # =============================================================
    _f = None                    # janela Tk (None = nao inicializada)
    _canvas = None               # canvas de desenho
    _titulo = "APFJogos - Python Text Mode Emulator (PyTME)"

    qtd_colunas = 80
    qtd_linhas = 25
    font_size = 13
    # Fonte default: None significa "use a fonte fixa do sistema"
    # (TkFixedFont). E' a forma mais segura de garantir monoespacada.
    # Para forcar outra fonte, atribuir uma tupla (familia, tamanho, peso):
    #     Pytme.fonte = ('Consolas', 13, 'bold')
    fonte = None
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

    # CONFIGURACAO DE TAMANHO/POSICAO DO CURSOR (ajustaveis pelo usuario).
    # Os "factors" sao proporcoes do tamanho do caractere (0.0 a 1.0).
    # Os "offset" sao em pixels e permitem ajuste fino.
    # Para mudar o cursor, ajuste estes valores ANTES da primeira chamada
    # (antes da janela abrir). Exemplo:
    #     from PyTME import Pytme
    #     Pytme.cursor_width_factor = 1.0   # cursor cobrindo toda a coluna
    #     Pytme.cursor_height_factor = 0.25 # cursor mais alto
    cursor_width_factor = 1.0    # 0..1: fracao da largura do caractere
                                 #       (1.0 = mesma largura da coluna)
    cursor_height_factor = 0.12  # 0..1: fracao da altura do caractere
                                 #       (modo insert: linha fina embaixo)
    cursor_offset_x = 0          # pixels: ajuste fino horizontal
    cursor_offset_y = 0          # pixels: ajuste fino vertical (negativo sobe)

    # --- teclado ---
    key_pressed = None           # ultima tecla recebida (event.char)
    code_key_pressed = -1        # ultimo keycode recebido

    # _keys_down: conjunto de keycodes ATUALMENTE pressionados.
    # Usado por is_key_pressed para detectar "tem tecla apertada agora",
    # independente de autorepeat do SO.
    _keys_down = None
    # _key_history: lista ordenada (mais recente no fim) de keycodes
    # pressionados. Permite responder "qual a tecla mais recente que
    # ainda esta pressionada" mesmo quando o autorepeat envia
    # KeyRelease/KeyPress em rajada.
    _key_history = None
    # _key_chars: mapa keycode -> ultimo event.char observado para essa
    # tecla. Necessario porque event.char nao vem em todos os eventos
    # (autorepeat KeyRelease no X11, por exemplo).
    _key_chars = None

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

        # ============================================================
        # Configuracao de fonte com GARANTIA de monoespacada.
        # ============================================================
        # Estrategia:
        #  1. Se o usuario forneceu uma tupla em cls.fonte, usa ela.
        #  2. Senao, TENTA explicitamente uma lista de fontes
        #     monoespacadas conhecidas, na ordem. Para cada uma,
        #     verifica se realmente esta' monoespacada (largura de
        #     varios chars e' a mesma). So' aceita se passar no teste.
        cls._font_obj = None
        try:
            if cls.fonte is not None:
                # usuario forneceu tupla — aceita sem verificar
                fam = cls.fonte[0]
                tam = int(cls.fonte[1]) if len(cls.fonte) > 1 else cls.font_size
                peso = cls.fonte[2] if len(cls.fonte) > 2 else 'normal'
                cls._font_obj = _Font(family=fam, size=tam, weight=peso)
            else:
                # tenta familias conhecidas de fontes monoespacadas,
                # em ordem de preferencia por plataforma
                candidatas = [
                    'Consolas',           # Windows (preferida)
                    'Lucida Console',     # Windows fallback
                    'Courier New',        # Windows fallback
                    'Menlo',              # macOS
                    'Monaco',             # macOS fallback
                    'DejaVu Sans Mono',   # Linux
                    'Liberation Mono',    # Linux
                    'Courier',            # fallback geral
                ]
                for fam in candidatas:
                    try:
                        f = _Font(family=fam, size=cls.font_size,
                                  weight='normal')
                        # teste de monoespacamento: medir varios chars,
                        # incluindo estreitos (i, l) e largos (M, W)
                        larguras = [f.measure(ch) for ch in 'iWMl0.@']
                        if len(set(larguras)) == 1 and larguras[0] > 0:
                            # passou no teste: e' monoespacada de verdade
                            cls._font_obj = f
                            break
                    except Exception:
                        continue
                if cls._font_obj is None:
                    # ultimo recurso: TkFixedFont (mesmo que possa
                    # nao ser perfeita)
                    base = _tkFont.nametofont('TkFixedFont')
                    cls._font_obj = _Font(
                        family=base.actual('family'),
                        size=cls.font_size,
                        weight='normal',
                    )

            # Medicao da fonte resolvida.
            # char_width: largura real de um caractere monoespacado.
            # char_height: usamos a altura visual da letra (ascent +
            # descent), NAO o linespace (que inclui line gap extra).
            cls.char_width = cls._font_obj.measure('M')
            ascent = cls._font_obj.metrics('ascent')
            descent = cls._font_obj.metrics('descent')
            cls.char_height = ascent + descent
            cls._font_ascent = ascent
            cls._font_descent = descent
        except Exception:
            cls._font_obj = None
            cls._font_ascent = cls.char_height * 3 // 4
            cls._font_descent = cls.char_height - cls._font_ascent

        # Tamanho final do cursor calculado a partir dos factors.
        cls.cursor_width = max(1, int(cls.char_width * cls.cursor_width_factor))
        cls.cursor_height = max(1, int(cls.char_height * cls.cursor_height_factor))

        # Margens de desenho (px) — o canvas tem essa borda interna para
        # nao deixar caracteres encostados na moldura da janela.
        cls._margin_x = 2
        cls._margin_y = 1

        cls.width = cls.qtd_colunas * cls.char_width + 2 * cls._margin_x
        cls.height = cls.qtd_linhas * cls.char_height + 2 * cls._margin_y

        # opcoes comuns para items de texto.
        # IMPORTANTE: cada caractere e' ancorado no CENTRO da sua celula
        # (em vez de NW). Isso garante visual uniforme mesmo se a fonte
        # tiver pequenas variacoes — caracteres mais estreitos ficam
        # centralizados na coluna, sem aparentar "desalinhados".
        # Usamos o objeto Font (cls._font_obj), nao a tupla, para evitar
        # substituicoes silenciosas pelo Tk.
        cls._opcoes_do_texto = {
            "font": cls._font_obj if cls._font_obj is not None else cls.fonte,
            "anchor": _tk.CENTER,
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
        cls._key_history = []
        cls._key_chars = {}
        cls._pending_release = None

        # cria a matriz 2D de conteudo (qtd_linhas x qtd_colunas)
        cls._conteudo = [[' '] * cls.qtd_colunas for _ in range(cls.qtd_linhas)]

        # ============================================================
        # GRADE DE ITEMS DE TEXTO: um item por celula da tela.
        # Cada caractere e' ancorado no CENTRO da sua celula —
        # posicao = (margem + col*char_width + char_width/2,
        #            margem + lin*char_height + char_height/2)
        # ============================================================
        cls._cell_items = [[None] * cls.qtd_colunas
                           for _ in range(cls.qtd_linhas)]
        # _canvas_text: espelho do que esta realmente no canvas, para
        # evitar chamadas itemconfig desnecessarias (otimizacao).
        cls._canvas_text = [[' '] * cls.qtd_colunas
                            for _ in range(cls.qtd_linhas)]
        for lin in range(cls.qtd_linhas):
            for col in range(cls.qtd_colunas):
                cx = cls._margin_x + col * cls.char_width + cls.char_width // 2
                cy = cls._margin_y + lin * cls.char_height + cls.char_height // 2
                iid = cls._canvas.create_text(
                    cx, cy,
                    text=' ',
                    **cls._opcoes_do_texto
                )
                cls._cell_items[lin][col] = iid

        # ============================================================
        # CURSOR: dois items sobrepostos para efeito de inversao:
        #   _cursor_rect: retangulo na cor do texto (cobertura branca).
        #   _cursor_char: caractere atual sobre o retangulo, com cor de
        #                 fundo (preto). Efeito visual = letra invertida.
        # ============================================================
        cls._cursor_rect = cls._canvas.create_rectangle(
            0, 0, cls.cursor_width, cls.cursor_height,
            fill=cls.cursor_color, outline=cls.cursor_color,
            state='hidden'
        )
        cls._cursor_char = cls._canvas.create_text(
            0, 0, text=' ',
            fill=cls.BACK_GROUND_COLOR_DEFAULT,
            anchor=_tk.CENTER,
            font=cls._opcoes_do_texto['font'],
            state='hidden',
        )

        # conjuntos de "sujeira"
        cls._dirty_lines = set(range(cls.qtd_linhas))
        cls._cursor_dirty = True

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
        # ==========================================================
        # PAINT por celula (grade 80x25 de items de texto).
        # ==========================================================
        # Para cada linha "suja", atualiza somente as celulas que
        # REALMENTE mudaram (usa cache _canvas_text). O custo de
        # itemconfig e' pago so quando ha diferenca.
        if cls._dirty_lines:
            for linha in cls._dirty_lines:
                row_buffer = cls._conteudo[linha]
                row_canvas = cls._canvas_text[linha]
                row_items = cls._cell_items[linha]
                for col in range(cls.qtd_colunas):
                    novo = row_buffer[col]
                    if row_canvas[col] != novo:
                        cls._canvas.itemconfig(row_items[col], text=novo)
                        row_canvas[col] = novo
            cls._dirty_lines.clear()

        # ==========================================================
        # CURSOR: dois items sobrepostos para efeito de "inversao".
        # ==========================================================
        # cursor_rect: retangulo na cor do texto (branco).
        # cursor_char: o mesmo caractere que esta na celula, mas com
        #              cor invertida (cor de fundo, ex.: preto). Fica
        #              POR CIMA do retangulo.
        # Resultado visual: o caractere fica visivel "em vinheta"
        # invertida, sem ser tampado.
        if cls._cursor_dirty:
            if cls.cursor_on and cls.cursor_blink_visible:
                # Caractere atualmente sob o cursor
                ch_sob = cls._conteudo[cls.cursor_Y - 1][cls.cursor_X - 1]

                # Coordenadas da CELULA (topo-esquerda e centro)
                cell_x = cls._margin_x + (cls.cursor_X - 1) * cls.char_width
                cell_y = cls._margin_y + (cls.cursor_Y - 1) * cls.char_height
                cell_cx = cell_x + cls.char_width // 2
                cell_cy = cell_y + cls.char_height // 2

                if cls.cursor_insert:
                    # Modo INSERT: barra fina embaixo do caractere
                    # (na base da letra, alinhada ao descent da fonte).
                    # Largura = cursor_width_factor * char_width,
                    # centralizada horizontalmente na celula.
                    bar_w = cls.cursor_width
                    bar_h = cls.cursor_height
                    x1 = (cell_cx - bar_w // 2) + cls.cursor_offset_x
                    # A barra fica na base da celula, descida do bottom:
                    y2 = cell_y + cls.char_height + cls.cursor_offset_y
                    y1 = y2 - bar_h
                    x2 = x1 + bar_w
                    cls._canvas.coords(cls._cursor_rect, x1, y1, x2, y2)
                    cls._canvas.itemconfig(cls._cursor_rect, state='normal')
                    # No modo insert nao usamos o char invertido — a
                    # barra fina nao cobre a letra, entao ela continua
                    # visivel normalmente.
                    cls._canvas.itemconfig(cls._cursor_char, state='hidden')
                else:
                    # Modo OVERWRITE: bloco cobrindo a celula inteira.
                    # Como o bloco tampa a letra, desenhamos a letra com
                    # cor de fundo POR CIMA (efeito de inversao).
                    x1 = cell_x + cls.cursor_offset_x
                    y1 = cell_y + cls.cursor_offset_y
                    x2 = x1 + cls.char_width
                    y2 = y1 + cls.char_height
                    cls._canvas.coords(cls._cursor_rect, x1, y1, x2, y2)
                    cls._canvas.itemconfig(cls._cursor_rect, state='normal')
                    # Texto invertido CENTRADO na celula (ancora CENTER)
                    cls._canvas.coords(cls._cursor_char,
                                       cell_cx + cls.cursor_offset_x,
                                       cell_cy + cls.cursor_offset_y)
                    cls._canvas.itemconfig(
                        cls._cursor_char,
                        text=ch_sob,
                        fill=cls.BACK_GROUND_COLOR_DEFAULT,
                        state='normal'
                    )
            else:
                cls._canvas.itemconfig(cls._cursor_rect, state='hidden')
                cls._canvas.itemconfig(cls._cursor_char, state='hidden')
            cls._cursor_dirty = False

        # NAO chamamos update_idletasks aqui — deixa o Tk acumular as
        # mudancas e aplicar quando estiver ocioso. Quem precisa de
        # update sincrono — delay(), read_key(), is_key_pressed() —
        # chama _f.update() explicitamente.

    @classmethod
    def _mark_dirty_line(cls, linha_idx):
        """Marca uma linha (0-based) como suja para o proximo _paint."""
        cls._dirty_lines.add(linha_idx)

    @classmethod
    def _mark_all_dirty(cls):
        cls._dirty_lines = set(range(cls.qtd_linhas))
        cls._cursor_dirty = True

    @classmethod
    def _mark_cursor_dirty(cls):
        cls._cursor_dirty = True

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
        cls._cursor_dirty = True
        cls._paint()

    @classmethod
    def set_cursor_on(cls):
        cls._ensure_init()
        cls.cursor_on = True
        cls._cursor_dirty = True
        cls._paint()

    @classmethod
    def set_cursor_off(cls):
        cls._ensure_init()
        cls.cursor_on = False
        cls._cursor_dirty = True
        cls._paint()

    @classmethod
    def set_cursor_mode(cls, mode=True):
        cls._ensure_init()
        cls.cursor_on = mode
        cls._cursor_dirty = True
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
        cls._cursor_dirty = True
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
        # todas as linhas viraram sujas
        cls._dirty_lines = set(range(cls.qtd_linhas))

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
        # todas as linhas afetadas (0..linha-1) viraram sujas
        for i in range(linha):
            cls._dirty_lines.add(i)

    @classmethod
    def _carriage_return_line_feed(cls):
        cls.cursor_X = 1
        cls.cursor_Y += 1
        if cls.cursor_Y > cls.qtd_linhas:
            cls._insert_line_up(cls.qtd_linhas)
            cls.cursor_Y = cls.qtd_linhas
        cls._cursor_dirty = True

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
        cls._dirty_lines.add(y - 1)
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
                cls._dirty_lines.add(pos_y)
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
        """Forca o redesenho da tela. Igual ao paint() do PyTME.
        Marca toda a tela como suja, garantindo atualizacao completa."""
        cls._ensure_init()
        cls._mark_all_dirty()
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
        cls._cursor_dirty = True
        cls._paint()

    @classmethod
    def clr_eol(cls):
        cls._ensure_init()
        linha = cls.cursor_Y - 1
        for coluna in range(cls.cursor_X - 1, cls.qtd_colunas):
            cls._conteudo[linha][coluna] = ' '
        cls._dirty_lines.add(linha)
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
        # reconfigurar a cor dos itens persistentes (grade celular)
        for row in cls._cell_items:
            for iid in row:
                cls._canvas.itemconfig(iid, fill=cls.TEXT_COLOR_DEFAULT)
        # tambem ajusta cor do char invertido do cursor para o novo fundo
        try:
            cls._canvas.itemconfig(
                cls._cursor_char, fill=cls.BACK_GROUND_COLOR_DEFAULT)
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
        # ajusta cor do char invertido do cursor
        try:
            cls._canvas.itemconfig(cls._cursor_char, fill=back_ground_color)
        except Exception:
            pass
        cls._paint()

    @classmethod
    def set_text_color(cls, text_color=None):
        cls._ensure_init()
        if text_color is None:
            text_color = cls.TEXT_COLOR_DEFAULT
        cls._opcoes_do_texto["fill"] = text_color
        # reconfigurar a cor dos itens existentes
        for row in cls._cell_items:
            for iid in row:
                cls._canvas.itemconfig(iid, fill=text_color)
        # cursor_rect tambem usa cor de texto (cobertura branca)
        try:
            cls._canvas.itemconfig(
                cls._cursor_rect, fill=text_color, outline=text_color)
        except Exception:
            pass
        cls._paint()

    # =============================================================
    # impressao
    # =============================================================

    @classmethod
    def text(cls, *args):
        """Imprime um ou mais argumentos concatenados, na posicao atual do cursor.

        Comportamento na borda direita:
          - Em qualquer linha QUE NAO seja a ultima: ao chegar na coluna 81,
            sempre faz CRLF (wrap automatico para a proxima linha),
            independente de cursor_on/off. Nao ha' efeito colateral nessas
            linhas — wrap e' o comportamento natural.
          - Na ULTIMA linha (linha 25), o wrap forcaria um scroll
            (rolagem da tela para cima). Para evitar isso em jogos:
              * cursor ligado (cursor_on=True): rola normalmente.
                Comportamento de terminal.
              * cursor desligado (cursor_on=False): NAO rola. O cursor
                fica congelado na coluna 80 da ultima linha; escritas
                subsequentes sobrescrevem o caractere ali.
          - '\\n' explicito no texto sempre quebra linha, mesmo com cursor
            desligado. Quebras explicitas sempre valem.
        """
        cls._ensure_init()
        if not args:
            cls._paint()
            return
        s = ''.join(str(a) for a in args if a is not None)
        # filtra CR; trata \n como CRLF
        s = s.replace('\r', '')
        for ch in s:
            if ch == '\n':
                # quebra explicita sempre vale
                cls._carriage_return_line_feed()
                continue

            # se o cursor ja' esta "congelado" no canto inferior direito
            # por impressao anterior com cursor_off, sobrescreve no mesmo
            # lugar sem avancar de novo.
            if cls.cursor_X > cls.qtd_colunas:
                cls.cursor_X = cls.qtd_colunas

            cls._conteudo[cls.cursor_Y - 1][cls.cursor_X - 1] = ch
            cls._dirty_lines.add(cls.cursor_Y - 1)
            cls.cursor_X += 1
            if cls.cursor_X > cls.qtd_colunas:
                # Wrap automatico. Em qualquer linha EXCETO a ultima,
                # sempre faz CRLF (e' so' uma quebra de linha sem scroll).
                # Na ultima linha, o CRLF triggaria scroll — entao depende
                # do estado do cursor.
                if cls.cursor_Y < cls.qtd_linhas:
                    # wrap normal: pula pra' primeira coluna da proxima linha
                    cls._carriage_return_line_feed()
                else:
                    # estamos na ultima linha: wrap forcaria scroll
                    if cls.cursor_on:
                        # comportamento de terminal: rola
                        cls._carriage_return_line_feed()
                    else:
                        # cursor off: congela em (80, qtd_linhas) sem rolar
                        cls.cursor_X = cls.qtd_colunas
        cls._cursor_dirty = True
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
        # Limpa apenas o "ultimo evento isolado", NAO mexe em _keys_down /
        # _key_history. Esses sao mantidos pelo estado real do teclado.
        cls.key_pressed = None
        cls.code_key_pressed = -1

    @classmethod
    def set_key_released(cls):
        # Mantida por compatibilidade com PyTME, mas agora e' praticamente
        # um no-op para a logica de jogos: get_key_code_pressed() reflete
        # o estado atual real do teclado via _key_history, nao precisa ser
        # "limpada".
        cls._set_key_released()

    @classmethod
    def get_key_pressed(cls):
        # Preferencia: tecla mais recente que ainda esta pressionada.
        # Fallback: ultimo char registrado (caso _key_history esteja
        # vazio mas algum evento tenha chegado).
        if cls._key_history:
            ultimo = cls._key_history[-1]
            return cls._key_chars.get(ultimo, cls.key_pressed)
        return cls.key_pressed

    @classmethod
    def get_key_code_pressed(cls):
        # Mesma logica: prioriza a tecla mais recente em _key_history.
        # Isto resolve o caso "estou segurando direita, apertei cima e
        # soltei, agora get_key_code_pressed retorna direita corretamente"
        # mesmo apos o autorepeat zerar code_key_pressed.
        if cls._key_history:
            return cls._key_history[-1]
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
                # autorepeat: reverter o release falso
                cls._keys_down.add(prev_code)
                if prev_code not in cls._key_history:
                    cls._key_history.append(prev_code)
            cls._pending_release = None

        cls.key_pressed = event.char
        cls.code_key_pressed = event.keycode
        if event.keycode:
            cls._keys_down.add(event.keycode)
            # Mantem _key_history sem duplicatas: se essa tecla ja estava
            # na pilha (autorepeat), move ela para o topo.
            if event.keycode in cls._key_history:
                cls._key_history.remove(event.keycode)
            cls._key_history.append(event.keycode)
            if event.char:
                cls._key_chars[event.keycode] = event.char
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
        if event.keycode in cls._key_history:
            cls._key_history.remove(event.keycode)
        cls._set_key_released()

    @classmethod
    def _on_focus_out(cls, event):
        cls._keys_down.clear()
        cls._key_history.clear()
        cls._pending_release = None
        cls._set_key_released()

    @classmethod
    def is_key_pressed(cls):
        """Retorna True se ha uma tecla pressionada AGORA. Processa
        eventos pendentes antes de consultar — funciona dentro de
        laços apertados.

        Drena toda a fila de eventos pendentes (nao apenas um), o que
        garante que pares Release+Press de autorepeat X11 sejam
        processados juntos, evitando a janela momentanea em que
        _keys_down ficaria temporariamente vazio durante uma tecla
        mantida pressionada.
        """
        cls._ensure_init()
        try:
            # update() processa eventos pendentes. Em alguns sistemas
            # eventos podem chegar em lotes, entao chamamos algumas vezes
            # para garantir que todos os pares Press+Release de autorepeat
            # cheguem juntos.
            for _ in range(3):
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

                # redesenha a string a partir da posicao inicial. O cursor
                # FICA VISIVEL durante o redraw (apenas reposicionamos
                # logicamente). NAO desligamos cursor_on — assim ele nao
                # "pisca" entre uma tecla e outra.
                cls._stop_blink()
                cls.cursor_X, cls.cursor_Y = x0, y0
                cls.text(s)
                if ord_tecla == 8 or ord_tecla == 46:
                    cls.text(" ")

                # calcula nova posicao do cursor em funcao do index
                x_cursor = 1 + (x0 + index_string - 1) % cls.qtd_colunas
                y_cursor = y0 + (x0 + index_string - 1) // cls.qtd_colunas
                if y_cursor > cls.qtd_linhas:
                    y0 -= 1
                    y_cursor -= 1

                cls.cursor_X, cls.cursor_Y = x_cursor, y_cursor
                # garantia: cursor visivel agora, imediatamente apos mover.
                cls.cursor_blink_visible = True
                cls._cursor_dirty = True
                cls._paint()

                if ord_tecla == 13:    # ENTER
                    break

                # reinicia o ciclo de blink — o cursor JA esta visivel,
                # entao o blink so vai apagar/aparecer apos cursor_ticks ms.
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
# Aliases globais: permitem usar
#   from PyTME import *
# sem precisar escrever "Pytme." na frente de cada chamada.
# =============================================================

goto_xy = Pytme.goto_xy
set_cursor_on = Pytme.set_cursor_on
set_cursor_off = Pytme.set_cursor_off
set_cursor_mode = Pytme.set_cursor_mode
get_cursor_mode = Pytme.get_cursor_mode
get_cursor_X = Pytme.get_cursor_X
get_cursor_Y = Pytme.get_cursor_Y
show_cursor = Pytme.show_cursor

clr_scr = Pytme.clr_scr
clr_eol = Pytme.clr_eol

reset_colors = Pytme.reset_colors
set_back_ground_color = Pytme.set_back_ground_color
set_text_color = Pytme.set_text_color

text = Pytme.text
textln = Pytme.textln

delay = Pytme.delay

set_key_released = Pytme.set_key_released
get_key_pressed = Pytme.get_key_pressed
get_key_code_pressed = Pytme.get_key_code_pressed
is_key_pressed = Pytme.is_key_pressed
read_key = Pytme.read_key
type_text = Pytme.type_text
type_textln = Pytme.type_textln

# Compatibilidade extra com a API do PyTME:
carriage_return_line_feed = Pytme.carriage_return_line_feed
change_cursor_state = Pytme.change_cursor_state
insert_xy_to_eol = Pytme.insert_xy_to_eol
insert_text_xy_in_content = Pytme.insert_text_xy_in_content
paint = Pytme.paint
printing_text = Pytme.printing_text
zero_content = Pytme.zero_content
blinking_cursor = Pytme.blinking_cursor
on_key_pressed = Pytme.on_key_pressed
on_key_released = Pytme.on_key_released
typing_text = Pytme.typing_text
run_key_pressed = Pytme.run_key_pressed
typeTextln = Pytme.typeTextln

# "pytme" (minusculo) como sinonimo da classe Pytme, ao estilo do PyTME
# original que tinha uma instancia global chamada 'pytme'. Aqui nao e
# instancia (e' a propria classe), mas funciona igual para chamadas:
#     pytme.text("oi")    # equivalente a Pytme.text("oi")
pytme = Pytme
