"""
    Sokoban - usando PyTME

    Empurre as caixas ($) para os alvos (.). Quando uma caixa esta em
    um alvo, vira *. Voce so consegue empurrar uma caixa por vez, e nao
    pode empurrar contra parede ou outra caixa.

    Controles:
        Setas: movimenta
        U:     desfaz ultimo movimento
        R:     reinicia o nivel atual
        N:     proximo nivel (se ja resolveu)
        Q:     sai

    Tiles:
        # parede    . alvo    $ caixa    * caixa em alvo
        @ voce      + voce em cima de alvo    (espaco) chao
"""

from PyTME import *
import sys


# --- niveis (strings de mapa). cada linha tem ate 30 chars. ---
NIVEIS = [
    # nivel 1: trivial pra ensinar (1 caixa, 1 alvo)
    [
        "########",
        "#      #",
        "# @    #",
        "# $    #",
        "#    . #",
        "#      #",
        "########",
    ],
    # nivel 2: empurrar contra a parede (2 caixas)
    [
        "###########",
        "#         #",
        "#  $   .  #",
        "#  @      #",
        "#  $   .  #",
        "#         #",
        "###########",
    ],
    # nivel 3: contorno simples
    [
        "  #####  ",
        "  #   #  ",
        "###   ###",
        "# $ @ $ #",
        "#       #",
        "#  .  . #",
        "#########",
    ],
    # nivel 4: precisa pensar na ordem (3 caixas)
    [
        "  ######  ",
        "###    ###",
        "#  $$$   #",
        "# #    # #",
        "# . . .  #",
        "#   @    #",
        "##########",
    ],
    # nivel 5: 4 caixas, 4 alvos. Pede planejamento de rotas.
    [
        "############",
        "#   ##     #",
        "# $ $ $$ @ #",
        "## ###     #",
        " # ..  ## ##",
        " # .. ##    ",
        " ##  ##     ",
        "  ####      ",
    ],
]


# --- constantes ---
LARGURA = 80
ALTURA = 25
Y_HUD = 25


# --- estado ---
estado = {
    'nivel_idx': 0,
    'mapa': None,           # lista de listas de chars (mutavel)
    'mapa_base': None,      # idem, mas so com chao/parede/alvo (sem caixas/jogador)
    'player_pos': (0, 0),   # (col, lin) dentro do mapa
    'historico': [],        # lista de (mapa_snapshot, player_pos) para undo
    'movimentos': 0,
    'origem_x': 0,          # offset de tela onde o mapa comeca
    'origem_y': 0,
    'mapa_w': 0, 'mapa_h': 0,
    'vencido': False,
}


def parsear_nivel(linhas):
    """Recebe lista de strings (nivel) e devolve:
       (mapa_completo, mapa_base, player_pos, dim_w, dim_h).
       mapa_completo tem $, *, @, +; mapa_base tem so' #, ., ' '."""
    altura = len(linhas)
    largura = max(len(l) for l in linhas)
    mapa = []
    base = []
    player = (0, 0)
    for y, linha in enumerate(linhas):
        linha = linha.ljust(largura)
        row_m = list(linha)
        row_b = []
        for x, c in enumerate(linha):
            if c == '@':
                player = (x, y)
                row_b.append(' ')
                row_m[x] = '@'
            elif c == '+':
                player = (x, y)
                row_b.append('.')
                row_m[x] = '+'
            elif c == '$':
                row_b.append(' ')
            elif c == '*':
                row_b.append('.')
            elif c == '.':
                row_b.append('.')
            elif c == '#':
                row_b.append('#')
            else:
                row_b.append(' ')
        mapa.append(row_m)
        base.append(row_b)
    return mapa, base, player, largura, altura


def carregar_nivel(idx):
    nivel = NIVEIS[idx]
    mapa, base, player, w, h = parsear_nivel(nivel)
    estado['mapa'] = mapa
    estado['mapa_base'] = base
    estado['player_pos'] = player
    estado['mapa_w'] = w
    estado['mapa_h'] = h
    estado['historico'] = []
    estado['movimentos'] = 0
    estado['vencido'] = False
    # centralizar mapa na tela (entre linhas 3 e 23)
    estado['origem_x'] = max(2, (LARGURA - w) // 2)
    estado['origem_y'] = max(3, (ALTURA - 1 - h) // 2)


def desenhar_mapa():
    ox, oy = estado['origem_x'], estado['origem_y']
    for y, linha in enumerate(estado['mapa']):
        goto_xy(ox, oy + y)
        text(''.join(linha))


def desenhar_celula(x, y):
    """x,y sao coords no mapa. Desenha na tela."""
    ox, oy = estado['origem_x'], estado['origem_y']
    goto_xy(ox + x, oy + y)
    text(estado['mapa'][y][x])


def desenhar_borda_e_titulo():
    goto_xy(1, 1)
    text("+" + "-" * (LARGURA - 2) + "+")
    titulo = f" SOKOBAN  -  Nivel {estado['nivel_idx'] + 1}/{len(NIVEIS)} "
    x = (LARGURA - len(titulo)) // 2
    goto_xy(x, 1)
    text(titulo)
    goto_xy(1, 2)
    text("|" + " " * (LARGURA - 2) + "|")
    # bordas laterais
    for y in range(3, Y_HUD):
        goto_xy(1, y); text("|")
        goto_xy(LARGURA, y); text("|")


def desenhar_hud():
    goto_xy(1, Y_HUD)
    msg = (f" Movimentos: {estado['movimentos']:4d}   "
           f"Caixas faltando: {caixas_faltando():2d}   "
           f"[setas] move  [U] desfaz  [R] reinicia  [N] proximo  [Q] sai")
    text(msg[:78].ljust(78))


def caixas_faltando():
    """Quantas caixas ainda nao estao em alvo."""
    n = 0
    for y, linha in enumerate(estado['mapa']):
        for c in linha:
            if c == '$':
                n += 1
    return n


def venceu():
    return caixas_faltando() == 0


def get_celula(x, y):
    """Retorna o caractere efetivo em (x,y) — o que esta no mapa."""
    if 0 <= y < estado['mapa_h'] and 0 <= x < estado['mapa_w']:
        return estado['mapa'][y][x]
    return '#'  # fora dos limites = parede


def get_base(x, y):
    """Retorna o caractere base em (x,y) — o que tem embaixo das peças."""
    if 0 <= y < estado['mapa_h'] and 0 <= x < estado['mapa_w']:
        return estado['mapa_base'][y][x]
    return '#'


def snapshot():
    """Salva estado atual no historico (para undo)."""
    snap_mapa = [linha[:] for linha in estado['mapa']]
    estado['historico'].append((snap_mapa, estado['player_pos']))
    # limita historico a 50 movimentos
    if len(estado['historico']) > 50:
        estado['historico'].pop(0)


def desfazer():
    if not estado['historico']:
        return False
    snap_mapa, player_pos = estado['historico'].pop()
    estado['mapa'] = snap_mapa
    estado['player_pos'] = player_pos
    estado['movimentos'] = max(0, estado['movimentos'] - 1)
    return True


def mover(dx, dy):
    """Tenta mover o jogador em (dx,dy). Retorna True se moveu."""
    px, py = estado['player_pos']
    nx, ny = px + dx, py + dy
    destino = get_celula(nx, ny)

    # parede? nao move
    if destino == '#':
        return False

    # caixa? tenta empurrar
    if destino in ('$', '*'):
        bx, by = nx + dx, ny + dy
        atras = get_celula(bx, by)
        if atras in ('#', '$', '*'):
            return False  # parede ou outra caixa atras
        # salva pre-snapshot e empurra
        snapshot()
        # remove caixa da posicao atual (volta a' base de (nx,ny))
        estado['mapa'][ny][nx] = '@' if get_base(nx, ny) == ' ' else '+'
        # poe caixa na nova posicao
        estado['mapa'][by][bx] = '*' if get_base(bx, by) == '.' else '$'
        # restaura a posicao antiga do jogador
        estado['mapa'][py][px] = get_base(px, py)
        estado['player_pos'] = (nx, ny)
        estado['movimentos'] += 1
        # redesenha as 3 celulas afetadas
        desenhar_celula(px, py)
        desenhar_celula(nx, ny)
        desenhar_celula(bx, by)
        return True

    # chao ou alvo: anda
    if destino in (' ', '.'):
        snapshot()
        estado['mapa'][py][px] = get_base(px, py)
        estado['mapa'][ny][nx] = '@' if destino == ' ' else '+'
        estado['player_pos'] = (nx, ny)
        estado['movimentos'] += 1
        desenhar_celula(px, py)
        desenhar_celula(nx, ny)
        return True

    return False


def limpar_area_jogo():
    for y in range(3, Y_HUD):
        goto_xy(2, y)
        text(" " * (LARGURA - 2))


def tela_mensagem(linhas):
    """Caixa centralizada com mensagem."""
    w = max(len(l) for l in linhas) + 4
    h = len(linhas) + 2
    x = (LARGURA - w) // 2
    y = (ALTURA - h) // 2
    goto_xy(x, y); text("+" + "-" * (w - 2) + "+")
    for i, ln in enumerate(linhas):
        goto_xy(x, y + 1 + i)
        text("| " + ln.ljust(w - 4) + " |")
    goto_xy(x, y + 1 + len(linhas)); text("+" + "-" * (w - 2) + "+")


def tela_inicial():
    clr_scr()
    goto_xy(28, 6);  text("===========================")
    goto_xy(28, 7);  text("       S O K O B A N       ")
    goto_xy(28, 8);  text("===========================")
    goto_xy(15, 11); text("Empurre as caixas ($) ate' os alvos (.)")
    goto_xy(15, 12); text("Caixa em alvo vira *. Voce so' empurra, nunca puxa.")
    goto_xy(15, 14); text("Tiles:")
    goto_xy(17, 15); text("# parede   . alvo   $ caixa   * caixa em alvo")
    goto_xy(17, 16); text("@ voce     + voce em cima de alvo")
    goto_xy(15, 18); text("[setas] move   [U] desfaz   [R] reinicia")
    goto_xy(15, 19); text("[N] proximo nivel (apos resolver)   [Q] sai")
    goto_xy(20, 22); text("Pressione qualquer tecla para comecar...")
    set_key_released()
    read_key()


def tela_vitoria_nivel():
    msg = [
        "        NIVEL COMPLETO!         ",
        "",
        f"  Movimentos: {estado['movimentos']}",
        "",
        "  [N] proximo  [R] reinicia  [Q] sai",
    ]
    tela_mensagem(msg)


def tela_fim_dos_niveis():
    msg = [
        "    P A R A B E N S !",
        "",
        " Voce resolveu todos os niveis!",
    ]
    tela_mensagem(msg)


# codigos de tecla
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 37, 38, 39, 40
VK_U, VK_R, VK_N, VK_Q, VK_ESC = 85, 82, 78, 81, 27


def jogar():
    while True:
        clr_scr()
        set_cursor_off()
        desenhar_borda_e_titulo()
        carregar_nivel(estado['nivel_idx'])
        desenhar_mapa()
        desenhar_hud()

        while True:
            if venceu() and not estado['vencido']:
                estado['vencido'] = True
                desenhar_hud()
                tela_vitoria_nivel()

            set_key_released()
            read_key()
            codigo = get_key_code_pressed()

            if codigo == VK_Q or codigo == VK_ESC:
                return
            elif codigo == VK_R:
                break  # recomeca o nivel
            elif codigo == VK_N:
                if estado['vencido']:
                    if estado['nivel_idx'] + 1 < len(NIVEIS):
                        estado['nivel_idx'] += 1
                        break
                    else:
                        clr_scr()
                        desenhar_borda_e_titulo()
                        tela_fim_dos_niveis()
                        set_key_released()
                        read_key()
                        return
            elif codigo == VK_U:
                if not estado['vencido']:
                    if desfazer():
                        # nao da' pra' desfazer incremental, redesenha o mapa
                        limpar_area_jogo()
                        desenhar_mapa()
                        desenhar_hud()
            elif codigo == VK_LEFT and not estado['vencido']:
                if mover(-1, 0): desenhar_hud()
            elif codigo == VK_RIGHT and not estado['vencido']:
                if mover(1, 0): desenhar_hud()
            elif codigo == VK_UP and not estado['vencido']:
                if mover(0, -1): desenhar_hud()
            elif codigo == VK_DOWN and not estado['vencido']:
                if mover(0, 1): desenhar_hud()


# --- main ---
tela_inicial()
jogar()
