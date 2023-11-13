from PyTME import *


set_cursor_off()  # retira o cursor da tela
rand = random.seed()  # inicializa a semente randômica

# começa o loop geral do jogo
while True
	clr_scr()    # apaga a tela

	# inicializa variáveis
	pegou=False
	suaCoordenadaX = random.randint(1, 80)  # escolhe de 1 a 80
	suaCoordenadaY = random.randint(1, 25)  # escolhe de 1 a 25
	inimigoCoordenadaX = random.randint(1, 80)  # escolhe de 1 a 80
	inimigoCoordenadaY = random.randint(1, 25)  # escolhe de 1 a 25

	# mostra a posição inicial
	goto_xy(suaCoordenadaX, suaCoordenadaY)
	text("O")
	goto_xy(inimigoCoordenadaX, inimigoCoordenadaY)
	text("X")

	# espera 2 segundos para começar o jogo
	delay(2000)

	# começa o loop do jogo (gameloop)

while True

	# aqui vai entrar todo o código que queremos funcionar durante o jogo

	# leitura do teclado
	if (is_key_pressed())
	teclaPressionada = read_key()

	# calcula o movimento do nosso personagem
	if (teclaPressionada=='l'): suaCoordenadaX=suaCoordenadaX+1
	if (teclaPressionada=='j'): suaCoordenadaX=suaCoordenadaX-1
	if (teclaPressionada=='i'): suaCoordenadaY=suaCoordenadaY-1
	if (teclaPressionada=='k'): suaCoordenadaY=suaCoordenadaY+1

	# verifica limites de bordas
	if (suaCoordenadaX == 0) suaCoordenadaX = 1
	if (suaCoordenadaX == 81) suaCoordenadaX = 80
	if (suaCoordenadaY == 0) suaCoordenadaY = 1
	if (suaCoordenadaY == 26) suaCoordenadaY = 25

	# cálculo da Inteligência Artificial e Movimento do Inimigo
	if (inimigoCoordenadaX>suaCoordenadaX) inimigoCoordenadaX=inimigoCoordenadaX-1
	if (inimigoCoordenadaX<suaCoordenadaX) inimigoCoordenadaX=inimigoCoordenadaX+1
	if (inimigoCoordenadaY>suaCoordenadaY) inimigoCoordenadaY=inimigoCoordenadaY-1
	if (inimigoCoordenadaY<suaCoordenadaY) inimigoCoordenadaY=inimigoCoordenadaY+1

	# verifica colisão
	if ((inimigoCoordenadaX==suaCoordenadaX) && (inimigoCoordenadaY==suaCoordenadaY))
	pegou=True

	# apaga a tela e imprime os objetos na tela
	clr_scr()
	goto_xy(suaCoordenadaX,suaCoordenadaY)
	textln("O")
	goto_xy(inimigoCoordenadaX, inimigoCoordenadaY)
	textln("X")

	# imprime coordenada do objeto O
	goto_xy(30,25)
	text("Coordenada XY = (",suaCoordenadaX,",",suaCoordenadaY,") ")

	# ajusta a velocidade do jogo
	delay(40)

	} while ((teclaPressionada!='q') && (!pegou))  # termino do gameloop

	if (pegou) {  # se houve a colisão, então mostrar o efeito da colisão
	i=1        # valor inicial do contador
	do {
	goto_xy(suaCoordenadaX, suaCoordenadaY)
	text("O")
	delay(20)
	goto_xy(suaCoordenadaX, suaCoordenadaY)
	text("*")
	delay(20)
	goto_xy(suaCoordenadaX, suaCoordenadaY)
	text("#")
	delay(20)
	goto_xy(suaCoordenadaX, suaCoordenadaY)
	text("X")
	delay(20)
	i=i+1    # soma o valor do contador
	} while (i<=10)
	goto_xy(3 2, 12)
	textln("VOCE PERDEU !!!!")
	textln()
	delay(2000)
	}

	#Pergunta se volta ou não ao início do jogo
	clr_scr()
	goto_xy(23,12)
	text("JOGAR NOVAMENTE? Sim ou Nao (s/n)?")
	do {  # repete até o jogador digitar "s" ou "n"
	teclaPressionada=read_key()
	} while ((teclaPressionada!='s') && (teclaPressionada!='n'))

	} while (teclaPressionada!='n')  # sai do jogo se digitar "n"
	clr_scr()
	goto_xy(28, 11)
	textln("Obrigado por jogar PegaPega")
	}

	}
