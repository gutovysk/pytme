"""
    Breakout (Quebra-blocos) - usando PyTME
    
    Controles:
        Setas esquerda/direita: move a raquete
        Espaco: lanca a bola
        Q: sai
        P: pausa
    
    Objetivo: quebrar todos os blocos sem deixar a bola cair.
    Voce tem 3 vidas. Cada bloco vale 10 pontos.
"""
#from PyTME_v1_1 import *
#from PyTME import *
from PyTME import *
import random


# --- constantes ---
LARGURA = 80
ALTURA = 25

# area de jogo
X_MIN, X_MAX = 2, 79
Y_MIN_TOPO = 2          # primeira linha jogavel (depois da borda)
Y_LINHA_RAQUETE = 22    # raquete fica nesta linha
Y_HUD = 25

# blocos
BLOCO_Y_INICIO = 3
BLOCO_Y_FIM = 7         # ate aqui (inclusive) tem blocos
BLOCO_LARGURA = 7       # cada bloco ocupa 7 colunas
BLOCO_GAP_X = 1         # 1 col de espaco entre blocos
# 10 blocos por linha: 10 * 7 + 9 * 1 = 79 colunas. Centralizado de 2 a 80.
NUM_COLUNAS_BLOCOS = 10
BLOCO_X_INICIO = 2

RAQUETE_LARGURA = 8
RAQUETE_CARACTER = "="

VELOCIDADE_MS = 60      # ms entre frames

# codigos de tecla
VK_LEFT = 37
VK_RIGHT = 39
VK_SPACE = 32
VK_Q = 81
VK_P = 80


# --- estado ---
blocos = []             # lista de retangulos [(x_ini, x_fim, y, viva)]
raquete_x = 0           # coluna mais a esquerda da raquete
bola_x = 0
bola_y = 0
bola_dx = 1
bola_dy = -1
bola_presa = True       # antes de lancar, fica grudada na raquete
vidas = 3
pontos = 0
blocos_restantes = 0

set_cursor_off()  # retira o cursor da tela

def desenhar_borda():
    goto_xy(1, 1)
    text("+" + "-" * (LARGURA - 2) + "+")
    for y in range(2, Y_HUD):
        goto_xy(1, y)
        text("|")
        goto_xy(LARGURA, y)
        text("|")
    # linha 25 e o HUD, nao desenhamos borda inferior aqui


def desenhar_hud():
    goto_xy(2, Y_HUD)
    msg = (" Pontos: " + str(pontos).ljust(5)
           + " Vidas: " + str(vidas)
           + " Blocos: " + str(blocos_restantes).ljust(3)
           + "   [<-][->] move  [Espaco] lanca  [P] pausa  [Q] sai")
    # garantir que cabe (78 chars max entre col 2 e 79)
    text(msg[:78].ljust(78))


def criar_blocos():
    global blocos, blocos_restantes
    blocos = []
    cores_simbolos = ["#", "@", "%", "&", "*"]  # so simbolos, sem cor
    for linha in range(BLOCO_Y_INICIO, BLOCO_Y_FIM + 1):
        idx_linha = linha - BLOCO_Y_INICIO
        simbolo = cores_simbolos[idx_linha % len(cores_simbolos)]
        for col in range(NUM_COLUNAS_BLOCOS):
            x_ini = BLOCO_X_INICIO + col * (BLOCO_LARGURA + BLOCO_GAP_X)
            x_fim = x_ini + BLOCO_LARGURA - 1
            blocos.append({
                'x_ini': x_ini, 'x_fim': x_fim,
                'y': linha, 'viva': True, 'simbolo': simbolo,
            })
    blocos_restantes = len(blocos)


def desenhar_blocos():
    for b in blocos:
        if b['viva']:
            goto_xy(b['x_ini'], b['y'])
            text(b['simbolo'] * BLOCO_LARGURA)


def apagar_bloco(b):
    goto_xy(b['x_ini'], b['y'])
    text(" " * BLOCO_LARGURA)


def desenhar_raquete():
    goto_xy(raquete_x, Y_LINHA_RAQUETE)
    text(RAQUETE_CARACTER * RAQUETE_LARGURA)


def apagar_raquete():
    goto_xy(raquete_x, Y_LINHA_RAQUETE)
    text(" " * RAQUETE_LARGURA)


def desenhar_bola():
    goto_xy(bola_x, bola_y)
    text("O")


def apagar_bola():
    goto_xy(bola_x, bola_y)
    text(" ")


def posicionar_bola_na_raquete():
    global bola_x, bola_y, bola_dx, bola_dy, bola_presa
    bola_x = raquete_x + RAQUETE_LARGURA // 2
    bola_y = Y_LINHA_RAQUETE - 1
    bola_dx = random.choice([-1, 1])
    bola_dy = -1
    bola_presa = True


def achar_bloco_em(x, y):
    for b in blocos:
        if b['viva'] and b['y'] == y and b['x_ini'] <= x <= b['x_fim']:
            return b
    return None


def mover_bola():
    """Move a bola um passo, tratando colisoes. Retorna:
       'ok', 'caiu' (perdeu vida), ou 'venceu' (todos blocos destruidos)."""
    global bola_x, bola_y, bola_dx, bola_dy, pontos, blocos_restantes

    novo_x = bola_x + bola_dx
    novo_y = bola_y + bola_dy

    # colisao com paredes laterais
    if novo_x < X_MIN:
        novo_x = X_MIN
        bola_dx = -bola_dx
    elif novo_x > X_MAX:
        novo_x = X_MAX
        bola_dx = -bola_dx

    # colisao com teto
    if novo_y < Y_MIN_TOPO:
        novo_y = Y_MIN_TOPO
        bola_dy = -bola_dy

    # caiu abaixo da raquete
    if novo_y >= Y_LINHA_RAQUETE + 1:
        return 'caiu'

    # colisao com raquete (linha logo acima)
    if novo_y == Y_LINHA_RAQUETE:
        if raquete_x <= novo_x < raquete_x + RAQUETE_LARGURA:
            # rebate. Define dx pela posicao relativa na raquete:
            # bordas esquerdas mandam pra esquerda, direitas pra direita
            pos_rel = novo_x - raquete_x  # 0..RAQUETE_LARGURA-1
            if pos_rel < RAQUETE_LARGURA // 3:
                bola_dx = -1
            elif pos_rel >= 2 * RAQUETE_LARGURA // 3:
                bola_dx = 1
            else:
                # meio: mantem direcao horizontal
                if bola_dx == 0:
                    bola_dx = random.choice([-1, 1])
            bola_dy = -1
            novo_y = Y_LINHA_RAQUETE - 1
            # nao precisa mais checar bloco neste passo

    # colisao com bloco
    bloco_atingido = achar_bloco_em(novo_x, novo_y)
    if bloco_atingido is not None:
        bloco_atingido['viva'] = False
        apagar_bloco(bloco_atingido)
        pontos += 10
        blocos_restantes -= 1
        bola_dy = -bola_dy
        # nao move pra dentro do bloco — recua um pouco
        novo_y = bola_y  # mantem y atual, so inverte direcao
        # se ainda assim houver bloco em (novo_x, novo_y), rebatemos tambem
        # (canto: pode acontecer raramente; ignoramos por simplicidade)
        if blocos_restantes == 0:
            apagar_bola()
            bola_x, bola_y = novo_x, novo_y
            return 'venceu'

    # desenha movimento
    apagar_bola()
    bola_x, bola_y = novo_x, novo_y
    desenhar_bola()
    return 'ok'


def mover_raquete(direcao):
    """direcao: -1 esquerda, +1 direita."""
    global raquete_x, bola_x
    novo_x = raquete_x + direcao * 2  # raquete anda 2 colunas por tecla
    if novo_x < X_MIN:
        novo_x = X_MIN
    if novo_x + RAQUETE_LARGURA - 1 > X_MAX:
        novo_x = X_MAX - RAQUETE_LARGURA + 1
    if novo_x == raquete_x:
        return
    apagar_raquete()
    raquete_x = novo_x
    desenhar_raquete()
    # se bola esta presa, anda com a raquete
    if bola_presa:
        apagar_bola()
        bola_x = raquete_x + RAQUETE_LARGURA // 2
        desenhar_bola()


def tela_pausa():
    goto_xy(32, 12)
    text(" *** PAUSA - tecla para continuar *** ")
    set_key_released()
    read_key()
    goto_xy(32, 12)
    text("                                       ")


def tela_inicial():
    clr_scr()
    goto_xy(28, 8)
    text("==============================")
    goto_xy(28, 9)
    text("        B R E A K O U T       ")
    goto_xy(28, 10)
    text("==============================")
    goto_xy(15, 13)
    text("Mova a raquete com as SETAS. Pressione ESPACO para lancar a bola.")
    goto_xy(15, 14)
    text("Quebre todos os blocos sem deixar a bola cair. Voce tem 3 vidas.")
    goto_xy(15, 16)
    text("Teclas: [<-][->] move   [Espaco] lanca   [P] pausa   [Q] sai")
    goto_xy(20, 19)
    text("Pressione qualquer tecla para comecar...")
    set_key_released()
    read_key()


def tela_game_over(venceu):
    goto_xy(28, 11)
    text("+--------------------------+")
    goto_xy(28, 12)
    if venceu:
        text("|     V O C E  V E N C E U!|")
    else:
        text("|      G A M E   O V E R   |")
    goto_xy(28, 13)
    text("|                          |")
    goto_xy(28, 14)
    text("|  Pontos: " + str(pontos).ljust(16) + "|")
    goto_xy(28, 15)
    text("+--------------------------+")
    delay(2000)
    goto_xy(20, 18)
    text("Pressione qualquer tecla para sair.")
    set_key_released()
    read_key()


def inicializar_jogo():
    global raquete_x, vidas, pontos
    clr_scr()
    desenhar_borda()
    raquete_x = (LARGURA - RAQUETE_LARGURA) // 2
    desenhar_raquete()
    criar_blocos()
    desenhar_blocos()
    vidas = 3
    pontos = 0
    posicionar_bola_na_raquete()
    desenhar_bola()
    desenhar_hud()


def jogar():
    global vidas, bola_presa
    inicializar_jogo()

    while True:
        # ler teclado (nao-bloqueante)
        if is_key_pressed():
            codigo = get_key_code_pressed()
            tecla = get_key_pressed()
            set_key_released()
            if codigo == VK_Q:
                return False
            elif codigo == VK_P:
                tela_pausa()
                set_key_released()
                continue
            elif codigo == VK_LEFT:
                mover_raquete(-1)
            elif codigo == VK_RIGHT:
                mover_raquete(1)
            elif tecla == ' ' or codigo == VK_SPACE:
                if bola_presa:
                    bola_presa = False

        if not bola_presa:
            resultado = mover_bola()
            if resultado == 'caiu':
                vidas -= 1
                desenhar_hud()
                if vidas <= 0:
                    tela_game_over(venceu=False)
                    return True
                # pausa breve, repoe bola
                apagar_bola()
                delay(500)
                posicionar_bola_na_raquete()
                desenhar_bola()
            elif resultado == 'venceu':
                tela_game_over(venceu=True)
                return True

        delay(VELOCIDADE_MS)


# --- main ---
random.seed()
tela_inicial()
jogar()
