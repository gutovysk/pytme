"""
    Snake (Cobrinha) - usando PyTME
    
    Controles:
        Setas: muda direcao da cobra
        Q: sai do jogo
        P: pausa
    
    Objetivo: comer as "macas" (@) para crescer.
    Nao bata nas paredes nem em si mesmo.
"""

#from PyTME import *
from PyTME import *
import random


# --- constantes ---
LARGURA = 80
ALTURA = 25
# Area jogavel: (2,2) ate (79, 23). Linha 24 fica para HUD, linha 25
# reservada (a biblioteca evita escrever na ultima celula).
X_MIN, X_MAX = 2, 79
Y_MIN, Y_MAX = 2, 23

VELOCIDADE_INICIAL_MS = 120   # ms entre frames
ACELERACAO_POR_MACA = 3       # diminui ms a cada maca comida
VELOCIDADE_MINIMA_MS = 50     # nao deixa ficar absurdamente rapido

# codigos de tecla (event.keycode no Tk)
VK_LEFT = 37
VK_UP = 38
VK_RIGHT = 39
VK_DOWN = 40
VK_Q = 81
VK_P = 80
VK_ENTER = 13

# --- estado do jogo ---
cobra = []        # lista de (x,y); cobra[0] = cabeca
direcao = (1, 0)  # (dx, dy) — comeca indo para a direita
maca = None
pontos = 0
velocidade_ms = VELOCIDADE_INICIAL_MS


def desenhar_borda():
    # topo e fundo da area jogavel
    goto_xy(1, 1)
    text("+" + "-" * (LARGURA - 2) + "+")
    for y in range(2, ALTURA - 1):
        goto_xy(1, y)
        text("|")
        goto_xy(LARGURA, y)
        text("|")
    goto_xy(1, ALTURA - 1)
    text("+" + "-" * (LARGURA - 2) + "+")


def desenhar_hud():
    goto_xy(2, ALTURA)
    text(" Pontos: " + str(pontos).ljust(4)
         + " Tamanho: " + str(len(cobra)).ljust(4)
         + " Vel: " + str(velocidade_ms) + "ms"
         + "   [setas] move  [P] pausa  [Q] sai     ")


def celula_ocupada(x, y):
    return (x, y) in cobra


def nova_maca():
    global maca
    # gera ate achar uma celula livre
    while True:
        x = random.randint(X_MIN, X_MAX)
        y = random.randint(Y_MIN, Y_MAX)
        if not celula_ocupada(x, y):
            maca = (x, y)
            goto_xy(x, y)
            text("@")
            return


def inicializar_jogo():
    global cobra, direcao, pontos, velocidade_ms
    clr_scr()
    desenhar_borda()
    # cobra inicial: 5 segmentos horizontais no meio da tela
    cx, cy = LARGURA // 2, ALTURA // 2
    cobra = [(cx + i, cy) for i in range(4, -1, -1)]  # cabeca a direita
    # desenha cobra
    for i, (x, y) in enumerate(cobra):
        goto_xy(x, y)
        text("O" if i == 0 else "o")
    direcao = (1, 0)
    pontos = 0
    velocidade_ms = VELOCIDADE_INICIAL_MS
    nova_maca()
    desenhar_hud()


def ler_direcao_e_atualizar():
    """Le o teclado de forma nao-bloqueante. Se houver tecla, ajusta
    direcao/estado. Retorna 'continuar', 'sair' ou 'pausa'."""
    global direcao
    if not is_key_pressed():
        return 'continuar'
    codigo = get_key_code_pressed()
    # consumir a tecla para nao reprocessar no proximo frame
    set_key_released()

    if codigo == VK_Q:
        return 'sair'
    if codigo == VK_P:
        return 'pausa'

    dx, dy = direcao
    novo = None
    if codigo == VK_LEFT:
        novo = (-1, 0)
    elif codigo == VK_RIGHT:
        novo = (1, 0)
    elif codigo == VK_UP:
        novo = (0, -1)
    elif codigo == VK_DOWN:
        novo = (0, 1)

    if novo is not None:
        # nao deixa virar 180 graus (cobra nao pode entrar em si mesma
        # ao trocar de direcao diretamente)
        if (novo[0] != -dx) or (novo[1] != -dy):
            direcao = novo

    return 'continuar'


def passo():
    """Move a cobra um passo. Retorna 'ok', 'comeu' ou 'fim'."""
    global pontos, velocidade_ms

    cabeca_x, cabeca_y = cobra[0]
    dx, dy = direcao
    novo_x = cabeca_x + dx
    novo_y = cabeca_y + dy

    # colisao com a parede
    if novo_x < X_MIN or novo_x > X_MAX or novo_y < Y_MIN or novo_y > Y_MAX:
        return 'fim'

    # colisao com o proprio corpo (sem contar a ultima cauda, pois ela vai
    # sair da posicao agora — exceto se for comer maca)
    vai_comer = (novo_x, novo_y) == maca
    corpo_a_checar = cobra if vai_comer else cobra[:-1]
    if (novo_x, novo_y) in corpo_a_checar:
        return 'fim'

    # desenha nova cabeca
    cobra.insert(0, (novo_x, novo_y))
    # a antiga cabeca vira corpo
    goto_xy(cabeca_x, cabeca_y)
    text("o")
    # nova cabeca
    goto_xy(novo_x, novo_y)
    text("O")

    if vai_comer:
        pontos += 10
        velocidade_ms = max(VELOCIDADE_MINIMA_MS,
                            velocidade_ms - ACELERACAO_POR_MACA)
        nova_maca()
        desenhar_hud()
        return 'comeu'
    else:
        # remove a cauda
        cauda_x, cauda_y = cobra.pop()
        goto_xy(cauda_x, cauda_y)
        text(" ")
        return 'ok'


def tela_pausa():
    goto_xy(32, 12)
    text(" *** PAUSA - tecla para continuar *** ")
    # esperar uma tecla
    set_key_released()
    read_key()
    # apagar mensagem
    goto_xy(32, 12)
    text("                                       ")


def tela_game_over():
    # caixa de 26 colunas (linha = 26 chars incluindo as bordas + e |)
    goto_xy(28, 11)
    text("+------------------------+")
    goto_xy(28, 12)
    text("|      G A M E  O V E R  |")
    goto_xy(28, 13)
    text("|                        |")
    goto_xy(28, 14)
    text("|  Pontos: " + str(pontos).ljust(14) + "|")
    goto_xy(28, 15)
    text("+------------------------+")
    delay(1500)

    # pede o nome com cursor piscando
    goto_xy(20, 18)
    text("Seu nome (Enter para terminar): ")
    nome = type_text()  # usa o cursor piscante
    if not nome.strip():
        nome = "Anonimo"

    goto_xy(20, 20)
    text("Obrigado, " + nome + "! Pressione qualquer tecla para sair.")
    set_key_released()
    read_key()


def jogar():
    inicializar_jogo()
    # pequena contagem antes de comecar
    for n in (3, 2, 1):
        goto_xy(38, 12)
        text(" -> " + str(n) + " <- ")
        delay(700)
    goto_xy(38, 12)
    text("         ")
    set_key_released()
    set_cursor_off()

    while True:
        estado = ler_direcao_e_atualizar()
        if estado == 'sair':
            return False  # sair sem game over
        if estado == 'pausa':
            tela_pausa()
            set_key_released()
            continue

        resultado = passo()
        if resultado == 'fim':
            tela_game_over()
            return True

        delay(velocidade_ms)


def tela_inicial():
    clr_scr()
    goto_xy(28, 8)
    text("==============================")
    goto_xy(28, 9)
    text("           S N A K E          ")
    goto_xy(28, 10)
    text("==============================")
    goto_xy(20, 13)
    text("Use as SETAS para mover a cobra.")
    goto_xy(20, 14)
    text("Coma as @ para crescer. Nao bata nas paredes.")
    goto_xy(20, 15)
    text("Teclas: [P] pausa   [Q] sair")
    goto_xy(20, 18)
    text("Pressione qualquer tecla para comecar...")
    set_key_released()
    read_key()


# --- main ---
random.seed()
tela_inicial()
jogar()
