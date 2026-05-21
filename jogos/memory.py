"""
    Memory (Jogo da Memoria) - usando PyTME

    Tabuleiro 4x4 de cartas viradas. Vire duas por vez; se combinarem,
    ficam reveladas. Senao, voltam a virar. Encontre todos os pares no
    menor numero de jogadas.

    Controles:
        Setas:  move a carta selecionada
        Espaco ou Enter: vira a carta atual
        Q ou ESC: sai
"""

from PyTME import *
import random


# --- constantes ---
COLUNAS = 4
LINHAS = 4
TOTAL_CARTAS = COLUNAS * LINHAS   # 16 cartas, 8 pares
SIMBOLOS = "ABCDEFGH"             # 8 simbolos diferentes para os 8 pares

# tamanho de cada carta (uma "caixa" 5 colunas x 3 linhas)
CARTA_W = 7
CARTA_H = 3
# espaco entre cartas
GAP_X = 2
GAP_Y = 1

# canto superior esquerdo do tabuleiro na tela
# Tabuleiro total: 4 * 7 + 3 * 2 = 34 colunas, 4 * 3 + 3 * 1 = 15 linhas.
# Centralizar: x = (80-34)/2 = 23; y = (25-15)/2 + 2 = 7
TABULEIRO_X = 23
TABULEIRO_Y = 7

# codigos de tecla
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 37, 38, 39, 40
VK_SPACE, VK_ENTER = 32, 13
VK_Q, VK_ESC = 81, 27


# --- estado ---
estado = {
    'cartas': [],            # lista de simbolos (16 itens, embaralhada)
    'reveladas': [],         # lista de bools paralela
    'selecionada': 0,        # indice 0..15 da carta sob o cursor
    'primeira_virada': -1,   # indice da carta virada na 1a jogada (ou -1)
    'jogadas': 0,
    'pares_achados': 0,
    'nome': "",
    'tempo_inicio': 0.0,
}


def inicializar_partida():
    pares = list(SIMBOLOS[:TOTAL_CARTAS // 2] * 2)  # ['A','A','B','B',...]
    random.shuffle(pares)
    estado['cartas'] = pares
    estado['reveladas'] = [False] * TOTAL_CARTAS
    estado['selecionada'] = 0
    estado['primeira_virada'] = -1
    estado['jogadas'] = 0
    estado['pares_achados'] = 0


def pos_carta(idx):
    """Retorna (x, y) na tela do canto superior esquerdo da carta idx."""
    col = idx % COLUNAS
    lin = idx // COLUNAS
    x = TABULEIRO_X + col * (CARTA_W + GAP_X)
    y = TABULEIRO_Y + lin * (CARTA_H + GAP_Y)
    return x, y


def desenhar_carta(idx, mostrar_face=None, selecionada=False):
    """Desenha a carta com sua moldura. Se selecionada=True, usa bordas
    duplas (==). mostrar_face: True/False/None.
       None = usa estado['reveladas'][idx]
       True = mostra letra (cara), False = mostra ?."""
    x, y = pos_carta(idx)
    if mostrar_face is None:
        mostrar_face = estado['reveladas'][idx]

    if selecionada:
        h_char, v_char, ne, nw, se, sw = "=", "H", "+", "+", "+", "+"
    else:
        h_char, v_char, ne, nw, se, sw = "-", "|", "+", "+", "+", "+"

    # topo
    goto_xy(x, y)
    text(nw + h_char * (CARTA_W - 2) + ne)
    # meio (2 linhas no nosso caso)
    for i in range(1, CARTA_H - 1):
        goto_xy(x, y + i)
        text(v_char + " " * (CARTA_W - 2) + v_char)
    # base
    goto_xy(x, y + CARTA_H - 1)
    text(sw + h_char * (CARTA_W - 2) + se)

    # conteudo
    centro_x = x + CARTA_W // 2
    centro_y = y + CARTA_H // 2
    if mostrar_face:
        c = estado['cartas'][idx]
    else:
        c = "?"
    goto_xy(centro_x, centro_y)
    text(c)


def redesenhar_tabuleiro():
    """Redesenha todas as 16 cartas (custa pouco)."""
    for idx in range(TOTAL_CARTAS):
        desenhar_carta(idx, selecionada=(idx == estado['selecionada']))


def redesenhar_carta_e_vizinha_anterior(antiga, nova):
    """Otimizacao: so' redesenha a antiga e a nova selecionada."""
    if antiga != nova:
        desenhar_carta(antiga, selecionada=False)
    desenhar_carta(nova, selecionada=True)


def desenhar_hud():
    goto_xy(1, 24)
    text("-" * 78)
    goto_xy(2, 25)
    msg = (f" {estado['nome'][:20]:20s}  "
           f"Jogadas: {estado['jogadas']:3d}   "
           f"Pares: {estado['pares_achados']}/{TOTAL_CARTAS // 2}   "
           f"[setas] move  [Espaco] vira  [Q] sai")
    text(msg[:78].ljust(78))


def desenhar_titulo():
    titulo = " JOGO DA MEMORIA "
    x = (80 - len(titulo)) // 2
    goto_xy(x, 2)
    text(titulo)
    goto_xy(2, 3)
    text("-" * 78)


def mover_selecao(dcol, dlin):
    idx = estado['selecionada']
    col = idx % COLUNAS
    lin = idx // COLUNAS
    novo_col = max(0, min(COLUNAS - 1, col + dcol))
    novo_lin = max(0, min(LINHAS - 1, lin + dlin))
    novo_idx = novo_lin * COLUNAS + novo_col
    if novo_idx != idx:
        antiga = idx
        estado['selecionada'] = novo_idx
        redesenhar_carta_e_vizinha_anterior(antiga, novo_idx)


def virar_carta_atual():
    """Tenta virar a carta selecionada. Logica do jogo."""
    idx = estado['selecionada']
    # ja revelada permanentemente? nao faz nada
    if estado['reveladas'][idx]:
        return
    # ja' e' a primeira virada? nao pode escolher a mesma duas vezes
    if estado['primeira_virada'] == idx:
        return

    if estado['primeira_virada'] == -1:
        # primeira carta do par: vira e segue
        estado['primeira_virada'] = idx
        # desenhar com face pra cima
        desenhar_carta(idx, mostrar_face=True, selecionada=True)
        return

    # segunda carta do par
    primeira = estado['primeira_virada']
    # vira a segunda visualmente
    desenhar_carta(idx, mostrar_face=True, selecionada=True)
    estado['jogadas'] += 1
    desenhar_hud()
    delay(800)  # tempo para o jogador ver as duas

    if estado['cartas'][primeira] == estado['cartas'][idx]:
        # par! ficam reveladas
        estado['reveladas'][primeira] = True
        estado['reveladas'][idx] = True
        estado['pares_achados'] += 1
        # redesenha para tirar destaque da primeira
        desenhar_carta(primeira, selecionada=False)
        desenhar_carta(idx, selecionada=(idx == estado['selecionada']))
    else:
        # nao combinaram: viram de volta
        desenhar_carta(primeira, mostrar_face=False, selecionada=False)
        desenhar_carta(idx, mostrar_face=False, selecionada=True)

    estado['primeira_virada'] = -1


def tela_pedir_nome():
    clr_scr()
    goto_xy(28, 6); text("==============================")
    goto_xy(28, 7); text("    J O G O   D A   M E M O R I A")
    goto_xy(28, 8); text("==============================")
    goto_xy(15, 11); text("Encontre todos os 8 pares de cartas.")
    goto_xy(15, 12); text("Vire duas por vez; se combinarem, ficam viradas.")
    goto_xy(15, 13); text("Tente fazer no menor numero de jogadas possivel.")
    goto_xy(15, 16); text("[setas] move o cursor   [Espaco/Enter] vira a carta")
    goto_xy(15, 17); text("[Q] ou [ESC] sai")
    goto_xy(15, 20); text("Seu nome (Enter): ")
    nome = type_text()
    nome = nome.strip()[:20]
    if not nome:
        nome = "Anonimo"
    return nome


def tela_vitoria():
    import time
    duracao = time.time() - estado['tempo_inicio']
    # box centralizado
    linhas = [
        "       P A R A B E N S !",
        "",
        f" {estado['nome']} venceu o jogo!",
        "",
        f"   Jogadas:  {estado['jogadas']}",
        f"   Tempo:    {int(duracao)}s",
        "",
        "  Pressione qualquer tecla para sair.",
    ]
    w = max(len(l) for l in linhas) + 4
    h = len(linhas) + 2
    x = (80 - w) // 2
    y = (25 - h) // 2
    goto_xy(x, y); text("+" + "-" * (w - 2) + "+")
    for i, ln in enumerate(linhas):
        goto_xy(x, y + 1 + i); text("| " + ln.ljust(w - 4) + " |")
    goto_xy(x, y + 1 + len(linhas)); text("+" + "-" * (w - 2) + "+")
    set_key_released()
    read_key()


def jogar():
    import time
    estado['nome'] = tela_pedir_nome()
    clr_scr()
    set_cursor_off()
    desenhar_titulo()
    inicializar_partida()
    estado['tempo_inicio'] = time.time()
    redesenhar_tabuleiro()
    desenhar_hud()

    while True:
        if estado['pares_achados'] >= TOTAL_CARTAS // 2:
            delay(500)
            tela_vitoria()
            return

        set_key_released()
        read_key()
        codigo = get_key_code_pressed()

        if codigo == VK_Q or codigo == VK_ESC:
            return
        elif codigo == VK_LEFT:
            mover_selecao(-1, 0)
        elif codigo == VK_RIGHT:
            mover_selecao(1, 0)
        elif codigo == VK_UP:
            mover_selecao(0, -1)
        elif codigo == VK_DOWN:
            mover_selecao(0, 1)
        elif codigo == VK_SPACE or codigo == VK_ENTER:
            virar_carta_atual()
            desenhar_hud()


# --- main ---
random.seed()
jogar()
